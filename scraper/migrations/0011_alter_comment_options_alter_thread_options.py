# Generated by Django 4.1.4 on 2023-03-14 19:52

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("scraper", "0010_comment_parent_comment_alter_comment_comment_id"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="comment",
            options={},
        ),
        migrations.AlterModelOptions(
            name="thread",
            options={},
        ),
    ]