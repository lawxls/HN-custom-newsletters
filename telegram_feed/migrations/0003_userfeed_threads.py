# Generated by Django 4.1 on 2022-10-30 18:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("scraper", "0002_thread_thread_created_at"),
        ("telegram_feed", "0002_telegramupdate"),
    ]

    operations = [
        migrations.AddField(
            model_name="userfeed",
            name="threads",
            field=models.ManyToManyField(related_name="user_feeds", to="scraper.thread"),
        ),
    ]
