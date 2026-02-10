from django.db.models.signals import post_save
from django.dispatch import receiver
import requests
import threading

from organizations.models import Assistant
from shop.services.comment_services import CommentService

#
# @receiver(post_save, sender=Assistant)
# def sync_assistant_to_ai_server(sender, instance, **kwargs):
#
#     def send_request():
#         training_data = CommentService.get_training_data(instance)
#
#         agent_id = "agent_3801kfxppx4kf8vvpg5xthybyz3f"
#
#         url = "http://161.35.153.151:8080/bot/sync-agent/"
#         payload = {
#             "agent_id": agent_id,
#             "training_data": training_data
#         }
#
#         try:
#             response = requests.post(url, json=payload, timeout=20)
#             if response.status_code == 200:
#                 print(f"Successfully synced agent {agent_id}")
#             else:
#                 print(f"Failed to sync agent: {response.text}")
#         except Exception as e:
#             print(f"Error connecting to AI server: {e}")
#
#     thread = threading.Thread(target=send_request)
#     thread.start()