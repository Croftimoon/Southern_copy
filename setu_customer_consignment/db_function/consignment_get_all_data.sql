DROP FUNCTION If EXISTS public.consignment_get_all_data(integer[], integer[], integer[], integer[], date, date);
CREATE OR REPLACE FUNCTION public.consignment_get_all_data(
IN company_ids integer[],
IN product_ids integer[],
IN category_ids integer[],
IN consignee_ids integer[],
IN start_date date,
IN end_date date)
RETURNS TABLE(consignee_id integer,
    			product_id integer,
    			product_name character varying,
				company_id integer,
    			company_name character varying,
				categ_id integer,
				category_name character varying,
				date_order timestamp,
				amount_total numeric,
				sold_quantity numeric,
				returned_qty numeric,
				trans_quantity numeric,
				sold_return_quantity numeric,
				sold_return_amount numeric,
				trans_amount numeric,
				return_amount numeric) AS
$BODY$
BEGIN
RETURN QUERY
select
	 t.consignee_id,
	 t.product_id,
	 t.product_name,
	 t.company_id,
	 t.company_name,
	 t.categ_id,
	 t.category_name,
	 t.date_order,
	 sum(t.amount_total) as amount_total,
	 sum(t.sold_quantity) as sold_quantity,
	 sum(t.returned_qty) as returned_qty,
	 sum(t.trans_quantity) as trans_quantity,
	 sum(t.sold_return_quantity) as sold_return_quantity,
	 sum(t.sold_return_amount) as sold_return_amount,
	 sum(t.trans_amount) as trans_amount,
	 sum(t.return_amount) as return_amount

from (

		SELECT
			so.partner_id as consignee_id,
			move.product_id,
			('['||prod.default_code||']'||' '||(tmpl.name ->>'en_US'))::character varying as product_name,
			so.company_id,
			cmp.name as company_name,
			tmpl.categ_id as categ_id,
			cat.complete_name as category_name,
			move.date as date_order,
			sum(Round((move.product_uom_qty * sol.price_unit) / CASE COALESCE(so.currency_rate, 0::numeric)
				WHEN 0 THEN 1.0
				ELSE so.currency_rate END, 2)) AS amount_total,
			sum(move.product_uom_qty) as sold_quantity,
			0 as returned_qty,
			0 as trans_quantity,
			0 as sold_return_quantity,
			0 as sold_return_amount,
			0 as trans_amount,
			0 as return_amount

			from stock_move move
			Inner Join sale_order_line sol on sol.id = move.sale_line_id
			Inner join sale_order so on so.id = sol.order_id
			Inner Join res_company cmp on cmp.id = move.company_id
			Inner Join product_product prod on prod.id = move.product_id
			Inner Join product_template tmpl on tmpl.id = prod.product_tmpl_id
			Inner Join product_category cat on cat.id = tmpl.categ_id
			LEFT JOIN res_partner rp ON so.partner_id = rp.id
			left join stock_location sl ON move.location_id = sl.id and sl.partner_id = rp.id
		WHERE so.property_is_consignment_order = True
			and so.partner_id is not null
			and move.state = 'done' and so.state in ('sale', 'done')
			and sl.partner_id is not null
			and move.date::date >= start_date and move.date::date <= end_date
			--company dynamic condition
			and 1 = case when array_length(company_ids,1) >= 1 then
				case when move.company_id = ANY(company_ids) then 1 else 0 end
				else 1 end
			--product dynamic condition
			and 1 = case when array_length(product_ids,1) >= 1 then
				case when move.product_id = ANY(product_ids) then 1 else 0 end
				else 1 end
			--category dynamic condition
			and 1 = case when array_length(category_ids,1) >= 1 then
				case when tmpl.categ_id = ANY(category_ids) then 1 else 0 end
				else 1 end
			--customer dynamic condition
			and 1 = case when array_length(consignee_ids,1) >= 1 then
				case when so.partner_id = ANY(consignee_ids) then 1 else 0 end
				else 1 end

		group by so.partner_id, so.company_id, move.product_id, move.date, cmp.name, prod.default_code, tmpl.name, tmpl.categ_id, cat.complete_name

		union all

		SELECT
			so.partner_id as consignee_id,
			move.product_id,
			('['||prod.default_code||']'||' '||(tmpl.name ->>'en_US'))::character varying as product_name,
			so.company_id,
			cmp.name as company_name,
			tmpl.categ_id as categ_id,
			cat.complete_name as category_name,
			move.date as date_order,
			0 AS amount_total,
			0 as sold_quantity,
			0 as returned_qty,
			0 as trans_quantity,
			(sum(move.product_uom_qty)) as sold_return_quantity,
			sum(Round((move.product_uom_qty * sol.price_unit) / CASE COALESCE(so.currency_rate, 0::numeric)
				WHEN 0 THEN 1.0
				ELSE so.currency_rate END, 2)) as sold_return_amount,
			0 as trans_amount,
			0 as return_amount

			from stock_move move
			Inner Join sale_order_line sol on sol.id = move.sale_line_id
			Inner join sale_order so on so.id = sol.order_id
			Inner Join res_company cmp on cmp.id = move.company_id
			Inner Join product_product prod on prod.id = move.product_id
			Inner Join product_template tmpl on tmpl.id = prod.product_tmpl_id
			Inner Join product_category cat on cat.id = tmpl.categ_id
			LEFT JOIN res_partner rp ON so.partner_id = rp.id
			left join stock_location sl ON move.location_dest_id = sl.id and sl.partner_id = rp.id
		WHERE so.property_is_consignment_order = True
			and so.partner_id is not null
			and move.state = 'done' and so.state in ('sale', 'done')
			and sl.partner_id is not null
			and move.date::date >= start_date and move.date::date <= end_date
			--company dynamic condition
			and 1 = case when array_length(company_ids,1) >= 1 then
				case when move.company_id = ANY(company_ids) then 1 else 0 end
				else 1 end
			--product dynamic condition
			and 1 = case when array_length(product_ids,1) >= 1 then
				case when move.product_id = ANY(product_ids) then 1 else 0 end
				else 1 end
			--category dynamic condition
			and 1 = case when array_length(category_ids,1) >= 1 then
				case when tmpl.categ_id = ANY(category_ids) then 1 else 0 end
				else 1 end
			--customer dynamic condition
			and 1 = case when array_length(consignee_ids,1) >= 1 then
				case when so.partner_id = ANY(consignee_ids) then 1 else 0 end
				else 1 end

		group by so.partner_id, so.company_id, move.product_id, move.date, cmp.name, prod.default_code, tmpl.name, tmpl.categ_id, cat.complete_name

		union all

		select
			sp.partner_id as consignee_id,
			move.product_id,
		    ('['||prod.default_code||']'||' '||(tmpl.name ->>'en_US'))::character varying as product_name,
			sp.company_id,
		    cmp.name as company_name,
			tmpl.categ_id as categ_id,
			cat.complete_name as category_name,
		    move.date as date_order,
			0 as amount_total,
			0 as sold_quantity,
			sum(move.product_uom_qty) as returned_qty,
			0 as trans_quantity,
			0 as sold_return_quantity,
			0 as sold_return_amount,
			0 as trans_amount,
			sum(move.product_uom_qty * tmpl.list_price) as return_amount

			from stock_move move
			left join stock_picking sp on sp.id = move.picking_id
			Inner Join res_company cmp on cmp.id = move.company_id
			Inner Join product_product prod on prod.id = move.product_id
			Inner Join product_template tmpl on tmpl.id = prod.product_tmpl_id
			Inner Join product_category cat on cat.id = tmpl.categ_id
			left join res_partner rp on rp.id = sp.partner_id
			left join stock_location sl ON sl.partner_id = rp.id and sp.location_id = sl.id
		where sl.is_consignment_location = True
			and sp.state in ('done')
			and sp.is_consignment_picking = True
			and move.date::date >= start_date and move.date::date <= end_date
			--company dynamic condition
			and 1 = case when array_length(company_ids,1) >= 1 then
				case when move.company_id = ANY(company_ids) then 1 else 0 end
				else 1 end
			--product dynamic condition
			and 1 = case when array_length(product_ids,1) >= 1 then
				case when move.product_id = ANY(product_ids) then 1 else 0 end
				else 1 end
			--category dynamic condition
			and 1 = case when array_length(category_ids,1) >= 1 then
				case when tmpl.categ_id = ANY(category_ids) then 1 else 0 end
				else 1 end
			--customer dynamic condition
			and 1 = case when array_length(consignee_ids,1) >= 1 then
				case when sp.partner_id = ANY(consignee_ids) then 1 else 0 end
				else 1 end
		group by sp.partner_id, sp.company_id, move.product_id, move.date, cmp.name, prod.default_code, tmpl.name, tmpl.categ_id, cat.complete_name

			UNION ALL

			select
			sp.partner_id as consignee_id,
			move.product_id,
			('['||prod.default_code||']'||' '||(tmpl.name ->>'en_US'))::character varying as product_name,
			sp.company_id,
			cmp.name as company_name,
			tmpl.categ_id as categ_id,
			cat.complete_name as category_name,
			move.date as date_order,
			0 as amount_total,
			0 as sold_quantity,
			0 as returned_qty,
			sum(move.product_uom_qty) as trans_quantity,
			0 as sold_return_quantity,
			0 as sold_return_amount,
			sum(move.product_uom_qty * tmpl.list_price) as trans_amount,
			0 as return_amount

			from stock_move move
			left join stock_picking sp on sp.id = move.picking_id
			Inner Join res_company cmp on cmp.id = move.company_id
			Inner Join product_product prod on prod.id = move.product_id
			Inner Join product_template tmpl on tmpl.id = prod.product_tmpl_id
			Inner Join product_category cat on cat.id = tmpl.categ_id
			left join res_partner rp on rp.id = sp.partner_id
			left join stock_location sl ON sl.partner_id = rp.id and sp.location_dest_id = sl.id
		where sl.is_consignment_location = True
			and sp.state in ('done')
			and sp.is_consignment_picking = True
			and move.date::date >= start_date and move.date::date <= end_date
			--company dynamic condition
			and 1 = case when array_length(company_ids,1) >= 1 then
				case when move.company_id = ANY(company_ids) then 1 else 0 end
				else 1 end
			--product dynamic condition
			and 1 = case when array_length(product_ids,1) >= 1 then
				case when move.product_id = ANY(product_ids) then 1 else 0 end
				else 1 end
			--category dynamic condition
			and 1 = case when array_length(category_ids,1) >= 1 then
				case when tmpl.categ_id = ANY(category_ids) then 1 else 0 end
				else 1 end
			--customer dynamic condition
			and 1 = case when array_length(consignee_ids,1) >= 1 then
				case when sp.partner_id = ANY(consignee_ids) then 1 else 0 end
				else 1 end
		group by sp.partner_id, sp.company_id, move.product_id, move.date, cmp.name, prod.default_code, tmpl.name, tmpl.categ_id, cat.complete_name
	)t
	group by t.consignee_id, t.company_id, t.product_id, t.date_order, t.company_name, t.product_name, t.categ_id, t.category_name;

END; $BODY$
LANGUAGE plpgsql VOLATILE
COST 100
ROWS 1000;