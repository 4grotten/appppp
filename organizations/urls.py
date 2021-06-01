from django.urls import path, include

from transactions.views.transaction_views import OrgFollowersTransactionsListAPIView
from .views.attendance_views import AttendanceUserInfoView, AttendanceView, AttendanceStatsView, GlobalAttendanceView
from .views.banner_views import BannerView, BannerDetailsView
from .views.card_views import DiscountsListBulkCreateAPIView, OrganizationDiscountsDeleteUpdateView, BackgroundListView
from .views.category_views import CategoryDetailAPIView
from .views.discount_views import DiscountsBulkUpdateView, DiscountsBulkDeleteView
from .views.hotlink_views import HotlinkListCreateView, HotlinkRetrieveUpdateDestroyView
from .views.membership_views import (
    MembershipListCreateView, RolesListCreateView, RoleRetrieveUpdateDestroyView,
    MembershipRetrieveUpdateDestroyView, TransferOwnershipView, BriefUserInfoView
)
from .views.organization_views import (
    OrganizationsListCreateView, OrganizationTypesListView, OrganizationRetrieveUpdateView,
    OrgMessageAPIView, OrgPhonesListAPIView, OrgNetworksListAPIView, SetOrganizationLocationAPIView,
    OrganizationTitleRetrieveAPIView, OrganizationFollowersCountAPIView, SubscriptionsMessageListAPIView,
    OrganizationsInCategoryView, HomepageOrganizationsView, HomepageSearchView, OrganizationPartnersCountAPIView,
    OrganizationPartnersFollowersCountAPIView, OrganizationAllTypesListView, InstagramIntegrationCreateRetrieveAPIView,
    InstagramAccountAPIView, InstagramParseLastDataAPIView, OrganizationCreationLimitView, DeactivateOrganizationView,
    ReactivateOrganizationView, ResetPurchaseIDView, OrganizationClientDetailsAPIView, DeliverySettingsView,
)
from .views.partnerships_views import (
    PartnershipView, OrganizationPartnersView, OrgPartnershipsView, PartnershipRetrieveUpdateDestroyView,
    HomepageRandomPartnersView, HomepagePartnersListView, HomepageBannersView, OrgPartnershipsInShortView,
)
from .views.seo_views import org_detail
from .views.subscription_views import SubscriptionsView, OrgFollowersListAPIView, OrgFollowersDetailsAPIView

organization_urls = [
    path('organization_types/', OrganizationTypesListView.as_view(), name='organization_types'),
    path('organization_all_types/', OrganizationAllTypesListView.as_view(), name='organization_types'),

    path('organizations/user_limits/', OrganizationCreationLimitView.as_view(), name='creation_limits'),
    path('organizations/', OrganizationsListCreateView.as_view(), name='user_organizations'),
    path('organizations/<int:pk>/', OrganizationRetrieveUpdateView.as_view(), name='organization_details'),
    path('organizations/<int:pk>/delivery_settings/', DeliverySettingsView.as_view(), name='delivery_settings'),
    path('organizations/<int:pk>/deactivate/', DeactivateOrganizationView.as_view(), name='deactivate_organization'),
    path('organizations/<int:pk>/reactivate/', ReactivateOrganizationView.as_view(), name='reactivate_organization'),
    path('organizations/<int:pk>/resetPurchaseID/', ResetPurchaseIDView.as_view(), name='reset_purchase_id'),
    path('organizations/<int:pk>/phone_numbers/', OrgPhonesListAPIView.as_view(), name='organization_phones'),
    path('organizations/<int:pk>/messages/', OrgMessageAPIView.as_view(), name='organization_messages'),
    path('messages/', SubscriptionsMessageListAPIView.as_view(), name='messages_all_subscriptions'),
    path('organizations/<int:pk>/social_networks/', OrgNetworksListAPIView.as_view(), name='organization_networks'),
    path('organizations/<int:pk>/location/', SetOrganizationLocationAPIView.as_view(), name='set_location'),
    path('organizations/<int:pk>/partners/', OrganizationPartnersView.as_view(), name='organization_partners'),
    path('organizations/<int:pk>/getOrganizationTitle/', OrganizationTitleRetrieveAPIView.as_view(), name='org_title'),
    path('organizations/<int:pk>/followers/', OrgFollowersListAPIView.as_view(), name='org_followers'),
    path('organizations/<int:organization_id>/clients/<int:user_id>/', OrganizationClientDetailsAPIView.as_view(),
         name='org_client_detail'),
    path('organizations/<int:organization_id>/followers/<int:user_id>/', OrgFollowersDetailsAPIView.as_view(),
         name='org_follower_detail'),
    path('organizations/<int:organization_id>/followers/<int:user_id>/transactions/',
         OrgFollowersTransactionsListAPIView.as_view(), name='org_followers_transactions'),
    path('organizations/<int:pk>/instagramIntegration/', InstagramIntegrationCreateRetrieveAPIView.as_view(),
         name='item_create'),
    path('organizations/<int:pk>/instagramUpdate/', InstagramParseLastDataAPIView.as_view(),
         name='last_instagram_data'),
    path('instagramCheckAccount/', InstagramAccountAPIView.as_view()),
    path('organizations/<int:pk>/getFollowersCount/', OrganizationFollowersCountAPIView.as_view(),
         name='org_followers_count'),
    path('organizations/<int:pk>/getPartnersCount/', OrganizationPartnersCountAPIView.as_view(),
         name="org_get_partners_count"),
    path(
        'organizations/<int:pk>/getPartnersFollowersCount/',
        OrganizationPartnersFollowersCountAPIView.as_view(),
        name="org_partners_followers_count"
    ),
]

membership_urls = [
    path('employees/', MembershipListCreateView.as_view(), name='organization_employees'),
    path('employees/<int:pk>/', MembershipRetrieveUpdateDestroyView.as_view(), name='employee_details'),
    path('roles/', RolesListCreateView.as_view(), name='organization_roles'),
    path('roles/<int:pk>/', RoleRetrieveUpdateDestroyView.as_view(), name='role_details'),
    path('employees/doTransferOwnership/', TransferOwnershipView.as_view(), name='ownership_transfer'),
    path('employees/user_info/<int:pk>/', BriefUserInfoView.as_view(), name='new_employee_info'),
]

attendance_urls = [
    path('attendance/user_info/', AttendanceUserInfoView.as_view(), name='employee_info'),
    path('attendance/', AttendanceView.as_view(), name='record_arrival'),
    path('global_attendance/', GlobalAttendanceView.as_view(), name='global_record_arrival'),
    path('employees/<int:pk>/attendance/', AttendanceStatsView.as_view(), name='attendance_stats'),
]

discounts_urls = [
    path('discounts/', DiscountsListBulkCreateAPIView.as_view(), name='discounts'),
    path('discounts/<int:pk>/', OrganizationDiscountsDeleteUpdateView.as_view(), name='discounts_delete'),
    path('discounts/doBulkUpdate/', DiscountsBulkUpdateView.as_view(), name='discounts_bulk_update'),
    path('discounts/doBulkDelete/', DiscountsBulkDeleteView.as_view(), name='discounts_bulk_delete'),
    path('discount_backgrounds/', BackgroundListView.as_view(), name='discount_backgrounds'),
]

partnership_urls = [
    path('partnerships/', PartnershipView.as_view(), name='partnerships'),
    path('partnerships/<int:pk>/', PartnershipRetrieveUpdateDestroyView.as_view(), name='partnership_details'),
    path('organizations/<int:pk>/partnerships/', OrgPartnershipsView.as_view(), name='organization_partnerships'),
    path('organizations/<int:pk>/partners_short_info/', OrgPartnershipsInShortView.as_view(),
         name='organization_editable_partnerships'),
]

homepage_urls = [
    path('homepage/partners/', HomepageRandomPartnersView.as_view(), name='homepage_partners'),
    path('homepage/ordered_partners/', HomepagePartnersListView.as_view(), name='homepage_partners_list'),
    path('homepage/banner_info/', HomepageBannersView.as_view(), name='homepage_banners'),
    path('homepage/organizations/', HomepageOrganizationsView.as_view(), name='homepage_organizations'),
    path('homepage/search/', HomepageSearchView.as_view(), name='homepage_search'),

    path('categorized_organizations/', OrganizationsInCategoryView.as_view(), name='categorized_organizations'),
]

banner_urls = [
    path('banners/', BannerView.as_view(), name='banners'),
    path('banners/<int:pk>/', BannerDetailsView.as_view(), name='banner_delete'),
]

hotlink_urls = [
    path('hotlinks/', HotlinkListCreateView.as_view(), name='hotlinks'),
    path('hotlinks/<int:pk>/', HotlinkRetrieveUpdateDestroyView.as_view(), name='hotlink_details'),
]

urlpatterns = [
    path('', include(organization_urls)),
    path('', include(membership_urls)),
    path('', include(attendance_urls)),
    path('', include(discounts_urls)),
    path('', include(partnership_urls)),
    path('', include(homepage_urls)),
    path('', include(banner_urls)),
    path('', include(hotlink_urls)),

    path('subscriptions/', SubscriptionsView.as_view(), name='subscriptions'),

    path('categories/<int:pk>/', CategoryDetailAPIView.as_view(), name='detail_category'),
    path('org_seo/<int:pk>/', org_detail)
]
