DROP FUNCTION if EXISTS public.consignment_ledger_analysis(integer[], integer[], integer[], integer[], date, date, integer);
CREATE OR REPLACE FUNCTION public.consignment_ledger_analysis(
    IN company_ids integer[],
    IN product_ids integer[],
    IN category_ids integer[],
    IN consignee_ids integer[],
    IN start_date date,
    IN end_date date,
    IN wizard_id integer)
  RETURNS void as
$BODY$
    DECLARE
        tr_start_date date;
        tr_end_date date;
        old_start_date date:= start_date;
        old_end_date date:= end_date;
        --start_date timestamp without time zone := (start_date || ' 00:00:00')::timestamp without time zone;
        --end_date timestamp without time zone:= (end_date || ' 23:59:59')::timestamp without time zone;
    BEGIN
        tr_start_date := '1900-01-01';
        tr_end_date := old_start_date - interval '1 day';

        with row_datas as (
            Select
                row_number() over(partition by T1.consignee_id, T1.product_id, T1.company_id order by T1.date_order::date, T1.consignee_id, T1.product_id, T1.company_id) as row_id,
                T1.consignee_id, T1.company_id, T1.company_name, T1.product_id, T1.product_name, T1.categ_id as product_category_id, T1.category_name,
                T1.date_order::date, sum(T1.opening_stock) as opening_stock, sum(T1.transferred_qty) as transferred_qty,
                sum(T1.sold_qty) as sold_qty,sum(T1.returned_qty) as returned_qty,
                sum(sum(T1.opening_stock) + sum(T1.transferred_qty) - sum(T1.sold_qty) - sum(T1.returned_qty) + sum(T1.sold_return_quantity))
                over(partition by T1.consignee_id, T1.product_id, T1.company_id order by T1.date_order::date, T1.consignee_id, T1.product_id, T1.company_id) as closing,
                sum(T1.sold_return_quantity) as sold_return_quantity
            From  (

            select
                C.consignee_id, C.company_id, C.company_name, C.product_id, C.product_name, c.categ_id, C.category_name,
                C.date_order::date as date_order, 0 as opening_stock, sum(C.trans_quantity) as transferred_qty,
                sum(C.sold_quantity) as sold_qty,sum(C.returned_qty) as returned_qty, sum(C.sold_return_quantity) as sold_return_quantity
                from consignment_get_all_data(company_ids, product_ids, category_ids, consignee_ids, start_date, end_date) C
                where
                --company dynamic condition
                1 = case when array_length(company_ids,1) >= 1 then
                    case when C.company_id = ANY(company_ids) then 1 else 0 end
                    else 1 end
                --product dynamic condition
                and 1 = case when array_length(product_ids,1) >= 1 then
                    case when C.product_id = ANY(product_ids) then 1 else 0 end
                    else 1 end
                --category dynamic condition
                and 1 = case when array_length(category_ids,1) >= 1 then
                    case when c.categ_id = ANY(category_ids) then 1 else 0 end
                    else 1 end
                --consignee dynamic condition
                and 1 = case when array_length(consignee_ids,1) >= 1 then
                    case when C.consignee_id = ANY(consignee_ids) then 1 else 0 end
                    else 1 end
                Group by C.consignee_id, C.company_id, C.company_name, C.product_id, C.product_name, c.categ_id, C.category_name, C.date_order::date

            --opening stock
            Union All

                select
                C.consignee_id, C.company_id, C.company_name, C.product_id, C.product_name, c.categ_id, C.category_name,
                old_start_date as date_order,
                    sum(sum(C.trans_quantity) - sum(C.sold_quantity) - sum(C.returned_qty) + sum(C.sold_return_quantity))
                over(partition by C.consignee_id, C.product_id, C.company_id order by C.date_order::date, C.consignee_id, C.product_id, C.company_id) as opening_stock,
                0 as transferred_qty,0 as sold_qty,0 as returned_qty, 0 as sold_return_quantity
                from consignment_get_all_data(company_ids, product_ids, category_ids, consignee_ids, tr_start_date, tr_end_date) C
                where
                --company dynamic condition
                1 = case when array_length(company_ids,1) >= 1 then
                    case when C.company_id = ANY(company_ids) then 1 else 0 end
                    else 1 end
                --product dynamic condition
                and 1 = case when array_length(product_ids,1) >= 1 then
                    case when C.product_id = ANY(product_ids) then 1 else 0 end
                    else 1 end
                --category dynamic condition
                and 1 = case when array_length(category_ids,1) >= 1 then
                    case when c.categ_id = ANY(category_ids) then 1 else 0 end
                    else 1 end
                --consignee dynamic condition
                and 1 = case when array_length(consignee_ids,1) >= 1 then
                    case when C.consignee_id = ANY(consignee_ids) then 1 else 0 end
                    else 1 end
                Group by C.consignee_id, C.company_id, C.company_name, C.product_id, C.product_name, c.categ_id, C.category_name, C.date_order::date
-------------------
--             Union All
--
--             select
--                 T.consignee_id, T.company_id, T.company_name, T.product_id, T.product_name, T.product_category_id, T.category_name,
--                 old_start_date as date_order, sum(T.opening_stock) as opening_stock, 0 as transferred_qty,
--                 0 as sold_qty,0 as returned_qty
--
--             from consignment_opening_analysis(company_ids, product_ids, category_ids, consignee_ids, tr_start_date, tr_end_date) T
--             Group by T.consignee_id, T.company_id, T.company_name, T.product_id, T.product_name, T.product_category_id, T.category_name
-------------------

            --T2
            --Group by T2.company_id, T2.company_name, T2.product_id, T2.product_name, T2.product_category_id, T2.category_name

        )T1
        Group by T1.consignee_id, T1.company_id, T1.company_name, T1.product_id, T1.product_name, T1.categ_id, T1.category_name, T1.date_order::date
    )

Insert into setu_consignment_ledger_bi_report(consignee_id, company_id, product_id, product_category_id, date_order, opening_stock, transferred_qty, sold_qty, returned_qty, closing, wizard_id, sold_return_quantity)
select
    d.consignee_id,
    d.company_id,
    d.product_id,
    d.product_category_id,
    d.date_order,
    d.opening_stock,
    d.transferred_qty,
    d.sold_qty,
    d.returned_qty,
    d.closing,
    wizard_id,
    d.sold_return_quantity
from (
select
		line_one.consignee_id, line_one.company_id, line_one.product_id, line_one.product_category_id, line_one.date_order::date,
    line_one.opening_stock, line_one.transferred_qty, line_one.sold_qty, line_one.returned_qty, line_one.closing, line_one.sold_return_quantity
	from
		row_datas line_one where line_one.row_id = 1
UNION ALL
select
	 r2.consignee_id, r2.company_id, r2.product_id, r2.product_category_id, r2.date_order::date,
    r1.closing as opening_stock, r2.transferred_qty, r2.sold_qty, r2.returned_qty, r2.closing, r2.sold_return_quantity
	from
		row_datas r1 join row_datas r2
            on r1.consignee_id = r2.consignee_id
            and r1.company_id = r2.company_id
            and r1.product_id = r2.product_id
            and r1.product_category_id = r2.product_category_id
            and r1.row_id = r2.row_id-1
	)d
order by 1,2,3,5;

    END;
$BODY$
LANGUAGE plpgsql VOLATILE
COST 100;