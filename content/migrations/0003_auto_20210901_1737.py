# Generated by Django 3.2.5 on 2021-09-01 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0002_post_horizontal'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='date_posted',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='commentresponse',
            name='date_posted',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
