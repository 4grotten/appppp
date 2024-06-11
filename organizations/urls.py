from django.urls import path, include
from rest_framework.routers import DefaultRouter

from transactions.views.transaction_views import OrgFollowersTransactionsListAPIView
from .views.assistant_views import OrganizationAssistantCreateView, OrganizationAssistantAnswerCreateView, \
    OrganizationAssistantAnswerRetrieveUpdateView, AnswerFileCreateView, QuestionListView, \
    OrganizationAssistantRetrieveUpdateView
from .views.attendance_views import AttendanceUserInfoView, AttendanceView, AttendanceStatsView, GlobalAttendanceView
from .views.banner_views import BannerView, BannerDetailsView
from .views.card_views import DiscountsListBulkCreateAPIView, OrganizationDiscountsDeleteUpdateView, BackgroundListView
from .views.category_views import CategoryDetailAPIView
from .views.discount_views import DiscountsBulkUpdateView, DiscountsBulkDeleteView
from .views.hotlink_views import (
    HotlinkListCreateView, HotlinkRetrieveUpdateDestroyView, HotlinkSubcategoriesListUpdateView,
    HotlinkItemsListUpdateView, CollectionLinksCreateView, CollectionLinksListView, CollectionLinkUpdateDestroyView,
    OrganizationHotlinkShopItems, OrganizationHotlinkSubcategories, HotlinkSelectedSubcategoriesListView
)
from .views.membership_views import (
    MembershipListCreateView, RolesListCreateView, RoleRetrieveUpdateDestroyView,
    MembershipRetrieveUpdateDestroyView, TransferOwnershipView, BriefUserInfoView
)
from .views.organization_promo_views import (
    OrganizationPromoRetrieveUpdateDestroyView, OrganizationPromoListCreateView, OrganizationPromoStatsView
)
from .views.organization_views import (
    OrganizationsListCreateView, OrganizationTypesListView, OrganizationRetrieveUpdateView,
    OrgMessageAPIView, OrgPhonesListAPIView, OrgNetworksListAPIView, SetOrganizationLocationAPIView,
    OrganizationTitleRetrieveAPIView, OrganizationFollowersCountAPIView, SubscriptionsMessageListAPIView,
    OrganizationsInCategoryView, HomepageOrganizationsView, OrganizationPartnersCountAPIView,
    OrganizationPartnersFollowersCountAPIView, OrganizationAllTypesListView, InstagramIntegrationCreateRetrieveAPIView,
    InstagramAccountAPIView, InstagramParseLastDataAPIView, OrganizationCreationLimitView, DeactivateOrganizationView,
    ReactivateOrganizationView, ResetPurchaseIDView, OrganizationClientDetailsAPIView, DeliverySettingsView,
    OrganizationsInServicesView, OrgVerifications, HomepageSearchView, OrganizationComplaintCreateView,
    OrganizationBlackListCreateView, OrganizationBlackListDestroyView, BlockUserCreateView, UnblockUserDestroyView,
    OrganizationsGoogleMapsCreateView, OrganizationsTwoGisCreateView, OrganizationPaymentSystemListView,
    PaymentSystemListView, OrgPaymentSystemConfirmation, OrganizationPaymentSystemsActivationView,
    OrganizationPaymentSystemsActivationDetailView, OrgWholesaleConfirmation, OrganizationsMapsListView,
    OrganizationMapsTypesListView, OrganizationsMapsCountryCityListView, MyOrganizationsWithCanEditListCreateView,
    MyOrganizationsListCreateView, OrganizationSubscriptionToGlobalAPIView, DeleteSubscriptionsAPIView
)
from .views.partnerships_views import (
    PartnershipView, OrganizationPartnersView, OrgPartnershipsListView, PartnershipRetrieveUpdateDestroyView,
    HomepageRandomPartnersView, HomepagePartnersListView, HomepageBannersView, OrgPartnershipsInShortView,
)
from .views.seo_views import org_detail
from .views.service import ServiceReadOnlySet, NonEmptyServiceCategoryItemListView
from .views.subscription_views import (
    SubscriptionsView, OrgFollowersListAPIView, OrgFollowersDetailsAPIView,
    MassPartnershipSubscriptionView, OrgDownloadFollowersAPIView, AcceptFollowerView, AcceptAllFollowersView,
    OrgBlockedUsersListAPIView, OrgBlockedDetailsAPIView
)

router = DefaultRouter()
router.register('services', ServiceReadOnlySet)

organization_urls = [
    path('services/<int:pk>/item_categories/', NonEmptyServiceCategoryItemListView.as_view(),
         name='service_item_category'),

    path('organization_types/', OrganizationTypesListView.as_view(), name='organization_types'),
    path('organization_all_types/', OrganizationAllTypesListView.as_view(), name='organization_types'),
    path('organizations/maps/types/', OrganizationMapsTypesListView.as_view(), name='organization_types'),

    path('organizations/user_limits/', OrganizationCreationLimitView.as_view(), name='creation_limits'),
    path('organizations/', OrganizationsListCreateView.as_view(), name='user_organizations'),
    path('organizations/my/', MyOrganizationsWithCanEditListCreateView.as_view(), name='user_organizations'),
    path('organizations/telegram/my/', MyOrganizationsListCreateView.as_view(), name='organizations_list_for_telegram'),
    path('organizations/maps/', OrganizationsMapsListView.as_view(), name='organizations_maps'),
    path('organizations/maps/new/', OrganizationsMapsCountryCityListView.as_view(), name='organizations_maps'),
    path('organizations/google_maps/create/', OrganizationsGoogleMapsCreateView.as_view(),
         name='user_google_maps_organizations'),
    path('organizations/two_gis/create/', OrganizationsTwoGisCreateView.as_view(),
             name='user_two_gis_organizations'),
    path('organizations/<int:pk>/', OrganizationRetrieveUpdateView.as_view(), name='organization_details'),
    path('organization/<int:pk>/verifications/', OrgVerifications.as_view(), name='organizations_verifications'),
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
    path('organizations/<int:pk>/download_followers/', OrgDownloadFollowersAPIView.as_view(), name='org_followers'),
    path('organizations/<int:pk>/blocked_users/', OrgBlockedUsersListAPIView.as_view(), name='org_blocked_users'),
    path('organizations/<int:organization_id>/blocked_users/<int:user_id>/', OrgBlockedDetailsAPIView.as_view(),
         name='org_blocked_user_detail'),
    path('organizations/<int:pk>/payment_systems/', OrganizationPaymentSystemListView.as_view(),
         name='organization_payment_systems_list'),
    path('organizations/<int:pk>/payment_systems/confirmation/', OrgPaymentSystemConfirmation.as_view(),
         name='organization_payment_systems_confirmation'),
    path('organizations/<int:pk>/wholesale/confirmation/', OrgWholesaleConfirmation.as_view(),
         name='organization_wholesale_confirmation'),
    path('organizations/<int:pk>/payment_systems/activation/', OrganizationPaymentSystemsActivationView.as_view(),
         name='organization_payment_systems_activation'),
    path('organizations/<int:pk>/payment_systems/activation/detail/',
         OrganizationPaymentSystemsActivationDetailView.as_view(),
         name='organization_payment_systems_activation_detail'),
    path('organizations/payment_systems/', PaymentSystemListView.as_view(), name='payment_systems_list'),
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
    path('accept_follower/', AcceptFollowerView.as_view(), name='accept_follower'),
    path('organizations/<int:pk>/accept_all_followers/', AcceptAllFollowersView.as_view(), name='accept_all_followers'),
    path('organizations/complaints/', OrganizationComplaintCreateView.as_view(), name='organization_complaint_create'),
    path('organizations/blacklist/', OrganizationBlackListCreateView.as_view(), name='organization_blacklist_create'),
    path('organizations/blacklist/delete/<int:pk>/', OrganizationBlackListDestroyView.as_view(),
         name='organization_blacklist_delete'),
    path('organizations/block_user/', BlockUserCreateView.as_view(), name='block_user'),
    path('organizations/unblock_user/<int:user_id>/<int:organization_id>/', UnblockUserDestroyView.as_view(),
         name='unblock_user'),
    path('organizations/follow_to_global/', OrganizationSubscriptionToGlobalAPIView.as_view(), name='follow_to_global'),
    path('organizations/delete_followers/', DeleteSubscriptionsAPIView.as_view(), name='delete_followers'),

    # assistant urls
    path('organizations/assistant/', OrganizationAssistantCreateView.as_view(), name='org_assistant_create'),
    path('organizations/assistant/<int:pk>/', OrganizationAssistantRetrieveUpdateView.as_view(),
         name='org_assistant_retrieve_update'),
    path('organizations/assistant/questions/', QuestionListView.as_view(), name='org_assistant_questions'),
    path('organizations/assistant/questions/answer/', OrganizationAssistantAnswerCreateView.as_view(),
         name='org_assistant_question_answer'),
    path('organizations/assistant/questions/answer/<int:id>/', OrganizationAssistantAnswerRetrieveUpdateView.as_view(),
         name='org_assistant_question_answer_detail'),
    path('organizations/assistant/questions/answer/file/', AnswerFileCreateView.as_view(),
         name='org_assistant_question_answer_file')
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
    path('organizations/<int:pk>/partnerships/', OrgPartnershipsListView.as_view(), name='organization_partnerships'),
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
    path('organizations/<int:pk>/collection_items/', OrganizationHotlinkShopItems.as_view(),
         name='organization_hotlink_shop_items'),
    path('organizations/<int:pk>/collection_subcategories/', OrganizationHotlinkSubcategories.as_view(),
         name='organization_hotlink_shop_subcategories'),

    path('hotlinks/', HotlinkListCreateView.as_view(), name='hotlinks'),
    path('hotlinks/<int:pk>/', HotlinkRetrieveUpdateDestroyView.as_view(), name='hotlink_details'),
    path('hotlinks/<int:pk>/items/', HotlinkItemsListUpdateView.as_view(), name='hotlink_shop_items'),
    path('hotlinks/<int:pk>/subcategories/', HotlinkSubcategoriesListUpdateView.as_view(),
         name='hotlink_subcategories'),
    path('hotlinks/<int:pk>/selected_subcategories/', HotlinkSelectedSubcategoriesListView.as_view(),
         name='selected_collection_subcategories'),
    path('hotlinks/<int:pk>/links/', CollectionLinksListView.as_view(), name='hotlink_links_list'),
    path('hotlink_links/', CollectionLinksCreateView.as_view(), name='create_hotlink_link'),
    path('hotlink_links/<int:pk>/', CollectionLinkUpdateDestroyView.as_view(), name='delete_hotlink_link'),
]

organization_promo_urls = [
    path('promos/', OrganizationPromoListCreateView.as_view(), name='org_promo_list_create'),
    path('organizations/<int:org_id>/promo/', OrganizationPromoRetrieveUpdateDestroyView.as_view(), name='org_promo'),
    path('organizations/<int:org_id>/promo_stats/', OrganizationPromoStatsView.as_view(), name='promo_stats'),
]

services_urls = [
    path('service/<int:pk>/organizations/', OrganizationsInServicesView.as_view(), name='organizations_in_services')
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
    path('', include(organization_promo_urls)),
    path('', include(router.urls)),
    path('', include(services_urls)),

    path('subscriptions/', SubscriptionsView.as_view(), name='subscriptions'),
    path('subscriptions/subscribe_to_partners/', MassPartnershipSubscriptionView.as_view(),
         name='subscribe_to_partners'),

    path('categories/<int:pk>/', CategoryDetailAPIView.as_view(), name='detail_category'),
    path('org_seo/<int:pk>/', org_detail)
]
