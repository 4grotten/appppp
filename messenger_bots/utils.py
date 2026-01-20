import logging

logger = logging.getLogger(__name__)


def add_bot_link_to_contacts(organization, bot_username: str) -> bool:
    """
    Add or update Telegram bot link in organization's social contacts.

    Args:
        organization: Organization model instance
        bot_username: Bot username without @

    Returns:
        True if link was added/updated, False otherwise
    """
    if not bot_username:
        logger.warning(f"Cannot add bot link for org {organization.id}: bot_username is empty")
        return False

    from organizations.models import SocialNetworkContact

    bot_link = f"https://t.me/{bot_username}"
    existing_tg_link = organization.social_contacts.filter(url__icontains="t.me/").first()

    if not existing_tg_link:
        SocialNetworkContact.objects.create(
            organization=organization,
            url=bot_link,
        )
        logger.info(f"Added bot link to org {organization.id} contacts: {bot_link}")
        return True
    elif existing_tg_link.url != bot_link:
        existing_tg_link.url = bot_link
        existing_tg_link.save(update_fields=["url"])
        logger.info(f"Updated bot link in org {organization.id} contacts: {bot_link}")
        return True

    logger.info(f"Bot link already exists for org {organization.id}: {bot_link}")
    return False
