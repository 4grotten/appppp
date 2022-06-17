from stock.models import FormatCriteria, SizeFormat, CriteriaSubcategory


class StockService:

    @classmethod
    def get_criteria_by_subcategory_id(cls, subcategory_id):
        return CriteriaSubcategory.objects.filter(
            item_subcategories__id=subcategory_id)

    @classmethod
    def get_format_by_criteria_subcategory_id(cls, criteria_subcategory_id):
        return FormatCriteria.objects.filter(
            criteria_subcategories__id=criteria_subcategory_id)

    @classmethod
    def get_sizes_by_format_id(cls, format_criteria_id):
        return SizeFormat.objects.select_related('format_criteria').filter(
            format_criteria__id=format_criteria_id).order_by('order')
