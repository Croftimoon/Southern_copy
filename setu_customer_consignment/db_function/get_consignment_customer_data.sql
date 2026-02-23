DROP FUNCTION If EXISTS public.get_consignment_customer_data(integer[], integer[], integer[], integer[], date, date);
CREATE OR REPLACE FUNCTION public.get_consignment_customer_data(
    IN company_ids integer[],
    IN product_ids integer[],
    IN category_ids integer[],
    IN consignee_ids integer[],
    IN start_date date,
    IN end_date date
)
RETURNS TABLE(
    company_id integer,
    consignee_id integer,
	sold_amount numeric,
	sold_quantity numeric,
	returned_qty numeric,
	trans_quantity numeric,
	sold_pr numeric,
	returned_pr numeric,
	sold_return_quantity numeric,
	sold_return_amount numeric,
	trans_amount numeric,
	return_amount numeric,
	sold_return_pr numeric
) AS
$BODY$
BEGIN
    Return Query
    Select
        t_data.*
    From
    (
        Select
            T.company_id,
            T.consignee_id,
            sum(T.amount_total) as sold_amount,
            sum(T.sold_quantity) as sold_quantity,
            sum(T.returned_qty) as returned_qty,
            sum(T.trans_quantity) as trans_quantity,
            CASE WHEN sum(T.sold_quantity) = 0 THEN
                sum(T.sold_quantity)
            ELSE
                (sum(T.sold_quantity) * 100/sum(T.trans_quantity))
            END AS sold_pr,

            CASE WHEN sum(T.returned_qty) = 0 THEN
                sum(T.returned_qty)
            ELSE
                (sum(T.returned_qty) * 100/sum(T.trans_quantity))
            END AS returned_pr,
            sum(T.sold_return_quantity) as sold_return_quantity,
            sum(T.sold_return_amount) as sold_return_amount,
            sum(T.trans_amount) as trans_amount,
            sum(T.return_amount) as return_amount,

            CASE WHEN sum(T.sold_quantity) = 0 THEN
                sum(T.sold_quantity)
            ELSE
                CASE WHEN sum(T.sold_return_quantity) = 0 THEN
                    sum(T.sold_return_quantity)
                ELSE
                    (sum(T.sold_return_quantity) * 100/sum(T.sold_quantity))
                END
            END AS sold_return_pr
        from consignment_get_all_data(company_ids, product_ids, category_ids, consignee_ids, start_date, end_date) T
        group by  T.company_id, T.consignee_id
    )t_data;

END; $BODY$
LANGUAGE plpgsql VOLATILE
COST 100
ROWS 1000;