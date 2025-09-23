from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shop', '0106_auto_20240626_0946'),
        ('organizations', '0151_auto_20250609_0740'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('percent', models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('description', models.CharField(blank=True, max_length=300, null=True)),
                ('image', models.ImageField(upload_to='coupons/')),
                ('expire_date', models.DateTimeField(blank=True, null=True)),
                ('always_active', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('is_updating', models.BooleanField(default=False)),
                ('coupon_type', models.CharField(choices=[('discount', 'Скидка'), ('product', 'Товарный купон')], default='product', max_length=20)),
                ('discount', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='coupon', to='organizations.discountcard')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='coupon', to='shop.shopitem')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='organization',
            name='update_posts',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='CouponUsage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_used', models.BooleanField(default=True)),
                ('coupon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coupon_usage', to='organizations.coupon')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coupon_usage', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

