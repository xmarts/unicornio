## -*- coding: utf-8 -*-

from openerp import models, fields, api, _, tools
from odoo.tools.sql import drop_view_if_exists

class uniquotationprice_line(models.Model):
	_inherit="quotation.price.line"
	prueba= fields.Char('prueba')
	@api.multi
	def init(self):
		drop_view_if_exists(self._cr, 'quotation_price_line')
		self._cr.execute("""
			CREATE OR REPLACE FUNCTION pricelist_trg()
				  RETURNS trigger AS
				$BODY$ DECLARE 
				 v_categ integer;
				 v_quotation integer;
				 v_provider integer;
				 v_id integer;
				 v_utility double precision;
				 v_costo double precision;
				 v_RECORD RECORD;
				  v_logistic double precision;
				 v_value1 double precision;
				 v_value2 double precision;
				BEGIN
				
				IF TG_OP='INSERT' THEN
					select provider_id into v_provider from quotation_price where id=new.quotation_id ;
					select logistic into v_logistic from res_partner where id=v_provider;
					select id into v_id from res_partner_lines where categ_id =new.categ_id and partner_id=v_provider;
					  FOR v_RECORD IN (select pricelist_id, utility from res_partnerprice_lines where reslines_id=v_id )
						LOOP
						v_utility:=1-(v_RECORD.utility/100);
						v_value1:=1+ (v_logistic/100);
						v_costo:=(new.total*v_value1)/v_utility;
						
						--raise exception '%','utilidad:  '|| v_costo;
							INSERT INTO quotation_pricelist_line(
							     create_uid, quotationprice_id, write_uid, create_date, write_date, 
							   totals, pricelist_id)
							VALUES (new.create_uid, new.id, new.write_uid,  new.create_date, new.write_date,  
							     v_costo::double precision, v_RECORD.pricelist_id );
						END LOOP;
				END IF;
				IF TG_OP='UPDATE' THEN
					select provider_id into v_provider from quotation_price where id=new.quotation_id ;
					select logistic into v_logistic from res_partner where id=v_provider;
					select id into v_id from res_partner_lines where categ_id =new.categ_id and partner_id=v_provider;
					  FOR v_RECORD IN (select pricelist_id, utility from res_partnerprice_lines where reslines_id=v_id )
						LOOP
							v_utility:=1-(v_RECORD.utility/100);
							v_value1:=1+ (v_logistic/100);
							v_costo:=(new.total*v_value1)/v_utility;
							--raise exception '%','utilidad:  '|| v_costo;
							UPDATE quotation_pricelist_line SET totals=v_costo WHERE quotationprice_id=new.id AND pricelist_id=v_RECORD.pricelist_id;
								
						END LOOP;

				END IF;

				 RETURN NEW;
				END 

				; $BODY$
				  LANGUAGE plpgsql VOLATILE
				  COST 100;
				ALTER FUNCTION pricelist_trg()
				  OWNER TO odoo;



				CREATE TRIGGER pricelist_trg
				  AFTER INSERT OR UPDATE
				  ON quotation_price_line
				  FOR EACH ROW
				  EXECUTE PROCEDURE pricelist_trg();

	        """)