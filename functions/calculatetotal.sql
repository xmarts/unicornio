
CREATE OR REPLACE FUNCTION pricelist_trg()
  RETURNS trigger AS
$BODY$ DECLARE 
 v_categ integer;
 v_quotation integer;
 v_provider integer;
 v_id integer;
 v_utility double precision;
 v_costo double precision;
 v_sum double precision;
 v_RECORD RECORD;
BEGIN
/**
select * from quotation_pricelist_line;
select * from quotation_price_line;
select * from quotation_price
select * from res_partner_lines
select * from res_partnerprice_lines
*/
IF TG_OP='INSERT' THEN
	select provider_id into v_provider from quotation_price where id=new.quotation_id ;
	select id into v_id from res_partner_lines where categ_id =new.categ_id and partner_id=v_provider;
	  FOR v_RECORD IN (select pricelist_id, utility from res_partnerprice_lines where reslines_id=v_id )
		LOOP
		v_utility:=v_RECORD.utility/100;
		v_sum:=new.total+new.costo_logistic;
		v_costo:=(new.total*v_utility)+v_sum;
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
	select id into v_id from res_partner_lines where categ_id =new.categ_id and partner_id=v_provider;
	  FOR v_RECORD IN (select pricelist_id, utility from res_partnerprice_lines where reslines_id=v_id )
		LOOP
			v_utility:=v_RECORD.utility/100;
			v_sum:=new.total+new.costo_logistic;
			v_costo:=(new.total*v_utility)+v_sum;
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
  OWNER TO postgres;

CREATE TRIGGER pricelist_trg
  after INSERT or UPDATE
  ON quotation_price_line
  FOR EACH ROW
  EXECUTE PROCEDURE pricelist_trg();