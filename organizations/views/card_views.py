from rest_framework import status
from rest_framework.generics import ListAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.exceptions import NotAcceptableException
from common.models import File
from common.serializers import ImageSerializer
from organizations.models import DiscountCard
from organizations.serializers.card_serializers import DiscountBulkCreateSerializer, DiscountGroupSerializer, \
    DiscountCardUpdateSerializer, DiscountCardSerializer
from organizations.services.card_services import DiscountCardService
from organizations.services.organization_services import OrganizationService


class OrganizationDiscountsAPIView(ListAPIView):
    pagination_class = None
    permission_classes = (IsAuthenticated,)
    serializer_class = DiscountBulkCreateSerializer

    def list(self, request, *args, **kwargs):
        organization_id = request.GET.get('organization', None)

        if organization_id is None or organization_id == '':
            return Response(data={
                'message': 'Please provide organization id as a query parameter',
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        discounts = DiscountCardService.get_grouped_discounts(organization_id=organization_id)
        serializer = DiscountGroupSerializer(discounts)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        DiscountCardService.bulk_create_discounts(cards=serializer.validated_data['cards'],
                                                  organization=serializer.validated_data['organization'])

        return Response(data={
            'message': 'Successfully created',
        }, status=status.HTTP_201_CREATED)


class OrganizationDiscountsDeleteUpdateView(UpdateAPIView, DestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = DiscountCard.objects.all()
    serializer_class = DiscountCardUpdateSerializer

    def destroy(self, request, *args, **kwargs):
        discount = DiscountCardService.get(id=kwargs['pk'], is_published=True)
        DiscountCardService.delete_discount(discount=discount, user=request.user)
        if discount.type == DiscountCard.CUMULATIVE:
            DiscountCardService.organize_cumulative_cards(organization=discount.organization)

        return Response(data={
            'message': 'Successfully deleted',
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if not OrganizationService.user_can_edit_organization(organization_id=instance.organization.id,
                                                              user=request.user):
            raise NotAcceptableException('No rights to edit organization')

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        instance = serializer.save()
        data = DiscountCardSerializer(instance).data
        return Response(data)


class BackgroundListView(ListAPIView):
    pagination_class = None
    permission_classes = (IsAuthenticated,)
    serializer_class = ImageSerializer

    def list(self, request, *args, **kwargs):
        queryset = File.objects.filter(backgrounds__isnull=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)