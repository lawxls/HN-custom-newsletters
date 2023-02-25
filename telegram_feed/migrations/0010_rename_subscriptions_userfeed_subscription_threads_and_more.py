# Generated by Django 4.1.4 on 2023-02-25 20:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("scraper", "0008_comment_scraper_com_body_ecb520_hash"),
        ("telegram_feed", "0009_userfeed_subscriptions"),
    ]

    operations = [
        migrations.RenameField(
            model_name="userfeed",
            old_name="subscriptions",
            new_name="subscription_threads",
        ),
        migrations.AddField(
            model_name="userfeed",
            name="subscription_comments",
            field=models.ManyToManyField(
                related_name="subscription_user_feeds", to="scraper.comment"
            ),
        ),
    ]
