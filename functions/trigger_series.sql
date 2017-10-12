-- Function: invoice_sale_trg()

-- DROP FUNCTION invoice_sale_trg();

CREATE OR REPLACE FUNCTION invoice_sale_trg()
  RETURNS trigger AS
$BODY$ DECLARE 
 v_picking integer;
 v_operation integer;
 cur RECORD;
 v_serie character varying(90);
 v_noserie text;
 v_noserie2 text;
 apa boolean;
 conta integer;
 al RECORD;
BEGIN


	apa:=True;
	FOR cur  IN (select splot.name
from stock_picking pi
left join stock_pack_operation sp on sp.picking_id =pi.id
left join stock_pack_operation_lot spl on spl.operation_id=sp.id
left join stock_production_lot splot on splot.id=spl.lot_id
where  pi.origin=new.origin AND sp.product_id=new.product_id
)
	LOOP 	

			IF apa = True then
				v_noserie :=cur.name;
				apa:=False;
			ELSE
				v_noserie:=v_noserie ||', '|| cur.name;
			end if;
			
	END LOOP;
	
	
	new.serie:=v_noserie;

	
--update account_invoice_line set serie:=v_noserie where 

 RETURN NEW;
END 

; $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION invoice_sale_trg()
  OWNER TO postgres;



CREATE TRIGGER invoice_sale_trg
  BEFORE INSERT
  ON account_invoice_line
  FOR EACH ROW
  EXECUTE PROCEDURE invoice_sale_trg();
