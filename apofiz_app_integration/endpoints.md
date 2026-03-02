# API Endpoints

Актуально на: 2026-02-27

## Base URLs

- REST API: `https://apofiz.com/api/v1`
- Site base (для некоторых ссылок): `https://apofiz.com`
- Supabase Functions: `{VITE_SUPABASE_URL}/functions/v1/{functionName}`

## Supabase Edge Functions

- `POST /functions/v1/translate`
- `POST /functions/v1/text-to-speech`

## Auth / User

- `POST /otp/send/`
- `POST /otp/verify/`
- `POST /register_auth/`
- `POST /verify_code/`
- `POST /resend_code/`
- `POST /login/`
- `POST /init_profile/`
- `POST /set_password/`
- `POST /users/doChangePassword/`
- `GET /users/me/`
- `POST /logout/`
- `GET /users/get_email/`
- `POST /users/forgot_password_email/`
- `POST /users/forgot_password/`
- `POST /files/`
- `GET /users/{user_id}/social_networks/`
- `POST /users/social_networks/`
- `GET /users/{user_id}/phone_numbers/`
- `POST /users/phone_numbers/`

## Organizations

- `GET /organizations/{organization_id}`
- `GET /organizations/{organization_id}/banners/`
- `GET /organizations/{organization_id}/assistants/`
- `GET /organizations/{organization_id}/payment_systems/`
- `GET /organizations/?page={page}&limit={limit}&search={search?}`
- `GET /homepage/search/?page={page}&limit={limit}&search={search?}`
- `POST /subscriptions/`

## Apofiz App Integration (new)

- `GET /apofiz/app/integration/organizations/link/?organization_id={organization_id}`
- `POST /apofiz/app/integration/organizations/link/`
	- body: `{ "organization_id": 123, "include_applications": true }`

Что делает endpoint:
- принимает `organization_id`
- проверяет организацию во внешнем проекте через `GET /organizations/{organization_id}`
- возвращает готовые ссылки на внешний API
- опционально подтягивает список приложений организации через `GET /shop/organization_items/?organization={id}`

Response example:

```json
{
	"organization_id": 123,
	"exists": true,
	"organization_url": "https://apofiz.com/api/v1/organizations/123/",
	"applications_url": "https://apofiz.com/api/v1/shop/organization_items/?organization=123",
	"organization_page_url": "http://134.122.53.6:3010/organizations/123_Keddo",
	"partner_organization": {},
	"partner_organization_status": 200,
	"partner_applications": {},
	"partner_applications_status": 200
}
```

`organization_page_url` формируется как:
- `{APOFIZ_INTEGRATION_ORG_PAGE_BASE_URL}/{organization_id}_{organization_title}`
- пример: `http://134.122.53.6:3010/organizations/120_Keddo`

404 response:

```json
{
	"organization_id": 123,
	"exists": false,
	"organization_url": "https://apofiz.com/api/v1/organizations/123/",
	"applications_url": "https://apofiz.com/api/v1/shop/organization_items/?organization=123",
	"error": "Organization not found in partner API"
}
```

## Shop / Products

- `GET /shop/feed/?page&limit&subcategories&category&country&city&search&ordering&current_timestamp_lt&start_time&organization`
- `GET /shop/items/{product_id}/`
- `GET /get_stock_set_items/{product_id}/?page&limit`
- `GET /shop/organization_items/?organization={id}&page&limit&subcategories&ordering&search`
- `GET /shop/{organization_id}/subcategories/`
- `POST /shop/likes/`
- `GET /countries/`
- `GET /currency_conversion/?from_currency&to_currency&amount`
- `GET /languages/`

## Cart

- `GET /carts/`
- `GET /carts/{cart_id}/`
- `POST /carts/doChangeItemCount/`
- `PUT /carts/{cart_id}/`
- `DELETE /carts/{cart_id}/`

## Comments / Assistant / Chat Theme

- `GET /organizations/assistant/chat/?assistant={id}|organization={id}&user={id}`
- `GET /comments/chat/{chat_id}/?limit&page`
- `POST /comments/chat/{chat_id}/`
- `POST /comments/chat/{chat_id}/assistant/`
- `POST /comments/{message_id}/like/`
- `POST /comments/chat/{chat_id}/read/`
- `GET /comments/item/{item_id}/?limit&page`
- `POST /comments/item/{item_id}/`
- `GET /chat/{chat_id}/call-ai/?assistant={id?}`
- `GET /comments/change/upload_theme_image/`
- `POST /comments/change/upload_theme_image/`

## Discounts / Coupons

- `GET /discounts/?organization={organization_id}`
- `GET /discount_backgrounds/`
- `PUT /discounts/{discount_id}/`
- `GET /coupons/{organization_id}/list/`
- `POST /coupons/{coupon_id}/use/`

## Contacts

- `GET /contacts/?page&limit`
- `POST /contacts/`
- `GET /contacts/{id}/`
- `PATCH /contacts/{id}/`
- `DELETE /contacts/{id}/`
- `POST /contacts/{id}/avatar/`
- `DELETE /contacts/{id}/avatar/`

## Collections / Bookmarks / Hotlinks

- `GET /shop/collections/?page&limit&item&search`
- `POST /shop/collections/`
- `POST /shop/collections/{collection_id}/`
- `GET /shop/collections/{collection_id}/?page&limit`
- `GET /shop/collections/{collection_id}/update/`
- `PUT /shop/collections/{collection_id}/update/`
- `DELETE /shop/collections/{collection_id}/update/`
- `GET /shop/bookmarks/?page&limit`
- `POST /shop/bookmarks/`
- `GET /hotlinks/?organization={id}&page&limit`
- `GET /hotlinks/{id}/`
- `GET /shop/hotlink_items/{id}/?page&limit&subcategory`
- `GET /hotlinks/{id}/selected_subcategories/`

## Followers / Blocking

- `GET /organizations/{organization_id}/followers/?page&limit&showFollowers=true`
- `GET /organizations/{organization_id}/blocked_users/?page&limit`
- `GET /organizations/{organization_id}/followers/{follower_id}/`
- `POST /organizations/block_user/`
- `DELETE /organizations/unblock_user/{user_id}/{organization_id}/`
- `DELETE /accept_follower/`

## Notifications

- `GET /notifications/?page&limit&mode`
- `GET /notifications/settings/`
- `POST /notifications/settings/`
- `GET /notifications/statistics/`

## Messenger

- `POST /messenger/chats/delete/`
- `POST /messenger/chats/view/`
- `GET /messenger/users/?query`
- `POST /messenger/chats/`
- `GET /messenger/chats/?page&limit`
- `GET /messenger/chats/organization/`
- `GET /messenger/folders/`
- `POST /messenger/folders/`
- `POST /messenger/folders/{folder_id}/chats/`
- `DELETE /messenger/folders/{folder_id}/chats/{chat_id}/`
- `PUT /messenger/folders/{folder_id}/`
- `DELETE /messenger/folders/{folder_id}/`
- `GET /messenger/chats/{chat_id}/?page&limit`
- `POST /messenger/chats/{chat_id}/`
- `PUT /messenger/messages/{message_id}/`
- `DELETE /messenger/messages/{message_id}/`
- `POST /messenger/likes/`
- `POST /messenger/chats/{chat_id}/block/`
- `DELETE /messenger/chats/{chat_id}/block/`
- `POST /messenger/group/{group_id}/add-users/`
- `POST /messenger/group/{group_id}/change-role/`
- `POST /messenger/group/{group_id}/delete-users/`
- `PUT /messenger/group/{group_id}/`
- `POST /messenger/group/`

## Statistics

- `GET /statistics/transactions/{transaction_id}/`
- `GET /organizations/{organization_id}/getOrganizationTitle/`
- `GET /statistics/totals/?organization={organization_id}`
- `GET /statistics/transactions/?page&limit&organization&search`
- `GET /statistics/unprocessedTranCount/`
- `GET /statistics/totals/`

## External URLs (outbound)

- `https://ai.gateway.lovable.dev/v1/chat/completions`
- `https://api.sws.speechify.com/v1/audio/speech`
- `https://api.speechify.ai/v1/audio/speech`

---

### Примечания

- `{...}` — динамические сегменты пути.
- Параметры после `?` часто опциональны и собираются динамически.
- Для некоторых путей поддерживаются несколько методов (например, настройки уведомлений, загрузка темы чата, update endpoint коллекций).
