from django.urls import path

from shop.views.cart_views import (
    CartItemCountChangeView, UserCartListView, OrderDeliveryView, TotalCartItemsCount,
    OrderSelfPickupView, UserCartRetrieveUpdateDestroyView, CartAnonymousCheckoutView,
    UpdateDeliveryToSendByCourierView, OnlinePaymentOrderDeliveryView
)
from shop.views.category_views import (
    ItemCategoryListView, ItemRentalCategoryListView, SubcategoryRetrieveUpdateDestroyView, ItemSubcategoryCreateView,
    OrganizationSubcategoryListView, NonEmptyCategoryListView, ItemCategoryRetrieveView,
    ItemCategoryAllSubcategoriesView, NonEmptyPartnerCategoryListView, NonEmptyPartnerSubcategoryListView,
    ItemTicketCategoryListView
)
from shop.views.comment_views import CommentItemListCreateView, \
    CommentDestroyUpdateRetrievtView, CommentedItemsListView, CommentLike, CommentComplaintCreateView
from shop.views.feed_views import (
    FeedView, OrganizationItemListView, SubscriptionItemListView, HotlinkCollectionItemListView,
    OrganizationRentalListView, OrganizationTicketListView, OrganizationOwnTicketListView
)
from shop.views.item_views import (
    ItemCreateView, ItemRentalCreateView, ItemRetrieveUpdateDestroyView, ItemChangePublishedStatusView,
    LikeListCreateView, BookmarkListCreateView, ComplaintCreateView, TranslateItemTextView, SuggestSearchItem,
    PartnerShopItemsListView, RentItemPeriodCreateView, RentalPeriodRetrieveView, GetYearsView, BookRentalView,
    BookingAnonymousCheckoutView, GetMonthsView, GetDaysView, GetHoursView, GetMinutesView, CollectionsListCreateView,
    AddRemoveListItemCollectionView, CollectionRetrieveUpdateDestroyView, ItemBookmarkBulkDeleteView,
    ItemTicketCreateView, TicketPeriodCreateView, ItemResumeCreateView, ResumeInfoUpdateView, ResumeInfoFileCreateView,
    ResumePhoneNumberUpdateView, ResumePhonesListAPIView, ResumeSocialNetworksUpdateView,
    ResumeSocialNetworksListAPIView, ResumeDetailInfoUpdateView, ResumeDetailInfoRetrieveAPIView,
    ResumeWorkExperienceListView, ResumeWorkExperienceUpdateView, ResumeInfoRetrieveAPIView, EducationListView,
    ResumeEducationListView, ResumeEducationUpdateView, SubmitResumeRequestView, AcceptResumeRequestView,
    DeclineResumeRequestView, UserResumeRequestRetrieveView, OrganizationSubmitResumeRequestView,
    OrganizationResumeRequestRetrieveView, TranslateNamesOfItemSubategoryV1
)

urlpatterns = [
    path('shop/categories/', ItemCategoryListView.as_view(), name='item_categories'),
    path('shop/categories/<int:pk>/', ItemCategoryRetrieveView.as_view(), name='item_category_details'),
    path('shop/categories/<int:pk>/all_subcategories/', ItemCategoryAllSubcategoriesView.as_view(),
         name='all_category_subcategories'),

    path('shop/rentals/categories/', ItemRentalCategoryListView.as_view(), name='rent_categories'),
    path('add_rental_period/<int:pk>/', RentItemPeriodCreateView.as_view(), name='add_rental_period'),
    path('get_rental_period/<int:pk>/', RentalPeriodRetrieveView.as_view(), name='rental_period_details'),
    path('shop/rentals/<int:pk>/years/', GetYearsView.as_view(), name='get_years'),
    path('shop/rentals/<int:pk>/months/', GetMonthsView.as_view(), name='get_months'),
    path('shop/rentals/<int:pk>/days/', GetDaysView.as_view(), name='get_days'),
    path('shop/rentals/<int:pk>/hours/', GetHoursView.as_view(), name='get_hours'),
    path('shop/rentals/<int:pk>/minutes/', GetMinutesView.as_view(), name='get_minutes'),

    path('shop/non_empty_categories/', NonEmptyCategoryListView.as_view(), name='non_empty_categories'),
    path('shop/non_empty_partner_categories/<int:pk>/', NonEmptyPartnerCategoryListView.as_view(), name='non_empty_partner_categories'),

    path('shop/subcategories/', ItemSubcategoryCreateView.as_view(), name='item_category_create'),
    path('shop/subcategories/<int:pk>/', SubcategoryRetrieveUpdateDestroyView.as_view(), name='subcategory_details'),
    path('shop/partner_subcategories/<int:pk>/', NonEmptyPartnerSubcategoryListView.as_view(), name='partner_subcategories'),

    path('shop/<int:pk>/subcategories/', OrganizationSubcategoryListView.as_view(), name='organization_subcategories'),

    path('shop/items/', ItemCreateView.as_view(), name='item_create'),
    path('shop/items/<str:pk>/', ItemRetrieveUpdateDestroyView.as_view(), name='item_details'),
    path('shop/doChangeItemPublishedStatus/', ItemChangePublishedStatusView.as_view(), name='item_published_status'),
    path('shop/translateItemText/', TranslateItemTextView.as_view(), name='translate_item_text'),

    path('shop/rentals/', ItemRentalCreateView.as_view(), name='rent_create'),
    path('shop/rentals/<int:pk>/booking/', BookRentalView.as_view(), name='rent_booking'),
    path('shop/rentals/<int:pk>/booking/offline_checkout/', BookingAnonymousCheckoutView.as_view(),
         name='booking_anonymous_checkout'),

    path('shop/tickets/', ItemTicketCreateView.as_view(), name='ticket_create'),
    path('shop/tickets/categories/', ItemTicketCategoryListView.as_view(), name='rent_categories'),
    path('shop/tickets/<int:pk>/ticket_period/', TicketPeriodCreateView.as_view(), name='add_ticket_period'),

    # resume API
    path('shop/resumes/', ItemResumeCreateView.as_view(), name='resume_create'),
    path('shop/resumes/files/', ResumeInfoFileCreateView.as_view(), name='resume_info_file_create'),
    path('shop/resumes/info/', ResumeInfoUpdateView.as_view(), name='resume_info_create'),
    path('shop/resumes/<int:pk>/info/', ResumeInfoRetrieveAPIView.as_view(), name='resume_info_retrieve'),
    path('shop/resumes/phone_numbers/', ResumePhoneNumberUpdateView.as_view(), name='resume_phone_numbers_create'),
    path('shop/resumes/<int:pk>/phone_numbers/', ResumePhonesListAPIView.as_view(), name='resume_phone_numbers_list'),
    path('shop/resumes/social_networks/', ResumeSocialNetworksUpdateView.as_view(),
         name='resume_social_networks_create'),
    path('shop/resumes/<int:pk>/social_networks/', ResumeSocialNetworksListAPIView.as_view(),
         name='resume_social_networks_list'),
    path('shop/resumes/detail_info/', ResumeDetailInfoUpdateView.as_view(),
         name='resume_detail_info_create'),
    path('shop/resumes/<int:pk>/detail_info/', ResumeDetailInfoRetrieveAPIView.as_view(),
         name='resume_detail_info_retrieve'),
    path('shop/resumes/work_experiences/', ResumeWorkExperienceUpdateView.as_view(),
         name='resume_work_experiences_list'),
    path('shop/resumes/<int:pk>/work_experiences/', ResumeWorkExperienceListView.as_view(),
         name='resume_work_experiences_list'),
    path('shop/resumes/educations/', ResumeEducationUpdateView.as_view(),
         name='resume_educations_list'),
    path('shop/resumes/<int:pk>/educations/', ResumeEducationListView.as_view(),
         name='resume_educations_list'),
    path('shop/educations/', EducationListView.as_view(), name='education_list'),
    path('shop/resume/user/request/', SubmitResumeRequestView.as_view(), name='resume_user_request'),
    path('shop/resume/user/request/<int:pk>/', UserResumeRequestRetrieveView.as_view(),
         name='resume_user_request_retrieve'),
    path('shop/resume/user/accept/', AcceptResumeRequestView.as_view(), name='resume_user_accept'),
    path('shop/resume/user/decline/', DeclineResumeRequestView.as_view(), name='resume_user_decline'),

    path('shop/resume/organization/request/', OrganizationSubmitResumeRequestView.as_view(),
         name='organization_resume_user_request'),
    path('shop/resume/organization/request/<int:pk>/', OrganizationResumeRequestRetrieveView.as_view(),
         name='resume_user_request_retrieve'),

    path('shop/feed/', FeedView.as_view(), name='shop_feed'),
    path('search/item/', SuggestSearchItem.as_view(), name='suggest_item'),
    path('shop/organization_items/', OrganizationItemListView.as_view(), name='organization_items'),
    path('shop/organization_rentals/', OrganizationRentalListView.as_view(), name='organization_rentals'),
    path('shop/organization_tickets/', OrganizationTicketListView.as_view(), name='organization_tickets'),
    path('shop/organization_tickets/own/', OrganizationOwnTicketListView.as_view(), name='own_organization_tickets'),
    path('shop/subscription_items/', SubscriptionItemListView.as_view(), name='subscribed_organization_items'),
    path('shop/hotlink_items/<int:pk>/', HotlinkCollectionItemListView.as_view(), name='hotlink_collection_items'),

    path('shop/likes/', LikeListCreateView.as_view(), name='like_list_create'),
    path('shop/bookmarks/', BookmarkListCreateView.as_view(), name='bookmark_list_create'),
    path('shop/bookmarks/delete/', ItemBookmarkBulkDeleteView.as_view(), name='bookmarks_delete'),
    path('shop/collections/', CollectionsListCreateView.as_view(), name='collection_list_create'),
    path('shop/collections/<int:pk>/', AddRemoveListItemCollectionView.as_view(),
         name='collection_add_remove_list_item'),
    path('shop/collections/<int:pk>/update/', CollectionRetrieveUpdateDestroyView.as_view(),
         name='collection_retrieve_update_delete'),
    path('shop/complaints/', ComplaintCreateView.as_view(), name='complaint_create'),

    path('carts/', UserCartListView.as_view(), name='user_cart_list'),
    path('carts/<int:pk>/', UserCartRetrieveUpdateDestroyView.as_view(), name='user_cart_details'),
    path('carts/doChangeItemCount/', CartItemCountChangeView.as_view(), name='add_cart_item'),
    path('carts/totalUserItemsCount/', TotalCartItemsCount.as_view(), name='all_cart_items_count'),
    path('carts/<int:pk>/delivery/', OrderDeliveryView.as_view(), name='order_delivery'),
    path('carts/<int:pk>/updateDelivery/', UpdateDeliveryToSendByCourierView.as_view(), name='order_delivery'),
    path('carts/<int:pk>/selfPickup/', OrderSelfPickupView.as_view(), name='order_self_pickup'),
    path('carts/<int:pk>/offline_checkout/', CartAnonymousCheckoutView.as_view(), name='cart_anonymous_checkout'),
    path('carts/<int:pk>/online_payment/', OnlinePaymentOrderDeliveryView.as_view(), name='order_online'),

    path('comments/item/<int:pk>/', CommentItemListCreateView.as_view(), name='comment_item_list'),
    path('comments/<int:pk>/', CommentDestroyUpdateRetrievtView.as_view(), name='comment_retrieve'),
    path('commented/items/', CommentedItemsListView.as_view(), name='commented_items'),
    path('comments/like/', CommentLike.as_view(), name='comment_like'),
    path('comments/complaints/', CommentComplaintCreateView.as_view(), name='comment_complaint_create'),

    path('partner_shop_items/<int:pk>/', PartnerShopItemsListView.as_view(), name='partner_shop_items'),
    path('translate_item_subcategory_names/', TranslateNamesOfItemSubategoryV1.as_view(),
         name='translate_item_subcategory_names')
]
