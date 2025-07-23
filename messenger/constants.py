PRIVATE = "private"
GROUP = "group"

CHAT_TYPES = [
    (PRIVATE, "Private"),
    (GROUP, "Group"),
]

ADMIN = "admin"
MEMBER = "member"

ROLE_CHOICES = [
    (ADMIN, "Admin"),
    (MEMBER, "Member"),
]

# ЧАТЫ
TRANSLATIONS = {
    "blocked": {
        "private": {
            "ru": "Заблокировал в чате",
            "en": "Blocked you in chat",
            "de": "Hat Sie im Chat blockiert",
            "tr": "Sizi sohbette engelledi",
            "zh": "在聊天中屏蔽了你",
        },
        "group": {
            "ru": "Заблокировал Вас в чате",
            "en": "Blocked you in chat",
            "de": "Hat Sie im Chat blockiert",
            "tr": "Sizi sohbette engelledi",
            "zh": "在聊天中屏蔽了你",
        },
    },
    "unblocked": {
        "private": {
            "ru": "Разблокировал в чате",
            "en": "Unblocked you in chat",
            "de": "Hat die Blockierung im Chat aufgehoben",
            "tr": "Sohbette engelinizi kaldırdı",
            "zh": "在聊天中取消了对你的屏蔽",
        },
        "group": {
            "ru": "Разблокировал Вас в чате",
            "en": "Unblocked you in chat",
            "de": "Hat die Blockierung im Chat aufgehoben",
            "tr": "Sohbette engelinizi kaldırdı",
            "zh": "在聊天中取消了对你的屏蔽",
        },
    },
    "appointed_admin": {
        "group": {
            "ru": "Назначил Вас администратором",
            "en": "Appointed you as an admin",
            "de": "Hat Sie zum Administrator ernannt",
            "tr": "Sizi yönetici olarak atadı",
            "zh": "已将你设为管理员",
        }
    },
    "removed_admin": {
        "group": {
            "ru": "Удалил вас из администратора",
            "en": "Removed you from admin",
            "de": "Hat Sie als Administrator entfernt",
            "tr": "Sizi yöneticilikten çıkardı",
            "zh": "已将你移除管理员",
        }
    },
    "added_member": {
        "group": {
            "ru": "Добавил Вас в группу",
            "en": "Added you to the group",
            "de": "Hat Sie zur Gruppe hinzugefügt",
            "tr": "Sizi gruba ekledi",
            "zh": "已将你添加到群组",
        }
    },
    "deleted_member": {
        "group": {
            "ru": "Удалил Вас с группы",
            "en": "Deleted you from the group",
            "de": "Hat Sie aus der Gruppe entfernt",
            "tr": "Sizi gruptan çıkardı",
            "zh": "已将你从群组移除",
        }
    },
}
