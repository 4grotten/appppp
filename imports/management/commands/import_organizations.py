from __future__ import print_function
import logging
import pandas as pd
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from common.models import Country
from organizations.models import Organization, OrganizationType, PhoneNumber
from organizations.services.organization_services import OrganizationInstagramIntegrationService




class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('-p', '--phone', dest='phone_number',
                            help='')
        parser.add_argument('-f', '--file', dest='path_to_file',
                            help='')

    def handle(self, *args, **options):
        phone_number = options['phone_number']
        file_path = options['path_to_file']
        try:
            user = User.objects.get(phone_number=phone_number)

        except User.DoesNotExist:
            print(f"User with phone number {phone_number} does not exist")


