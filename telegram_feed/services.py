import datetime
from collections.abc import Iterable, Mapping
from dataclasses import asdict
from time import sleep

from django.conf import settings
from django.db.models.query import QuerySet
from django.utils import timezone

from scraper.models import Comment, Thread
from telegram_feed.exceptions import BadOptionCombinationError, InvalidOptionError
from telegram_feed.models import Keyword, TelegramUpdate, UserFeed
from telegram_feed.requests import SendMessageRequest
from telegram_feed.types import InlineKeyboardButton, KeywordData
from telegram_feed.utils import escape_markdown


class RespondToMessageService:
    """telegram user text response logic"""

    START_COMMAND = "START_COMMAND"
    HELP_COMMAND = "HELP_COMMAND"
    LIST_KEYWORDS_COMMAND = "LIST_KEYWORDS_COMMAND"
    ADD_KEYWORD_COMMAND = "ADD_KEYWORD_COMMAND"
    REMOVE_KEYWORD_COMMAND = "REMOVE_KEYWORD_COMMAND"
    SET_SCORE_COMMAND = "SET_SCORE_COMMAND"
    STOP_COMMAND = "STOP_COMMAND"
    SUBSCRIBE_COMMAND = "SUBSCRIBE_COMMAND"
    UNSUBSCRIBE_COMMAND = "UNSUBSCRIBE_COMMAND"
    LIST_SUBSCRIPTIONS_COMMAND = "LIST_SUBSCRIPTIONS_COMMAND"
    FOLLOW_COMMAND = "FOLLOW_COMMAND"
    UNFOLLOW_COMMAND = "UNFOLLOW_COMMAND"
    DOMAINS_COMMAND = "DOMAINS_COMMAND"
    UNDEFINED_COMMAND = "UNDEFINED_COMMAND"

    def __init__(self, telegram_update: TelegramUpdate) -> None:
        self.telegram_update = telegram_update

        # create UserFeed by chat_id if it doesn't exist and set flag
        user_feed = UserFeed.objects.filter(chat_id=telegram_update.chat_id).first()
        user_feed_created = False
        if user_feed is None:
            user_feed = UserFeed.objects.create(chat_id=telegram_update.chat_id)
            user_feed_created = True

        self.user_feed = user_feed
        self.user_feed_created = user_feed_created

    def respond_to_user_message(self) -> str:
        user_message_type = self.check_user_message()

        match user_message_type:
            case self.START_COMMAND:
                return self.respond_to_start_and_help_command()
            case self.HELP_COMMAND:
                return self.respond_to_start_and_help_command()
            case self.LIST_KEYWORDS_COMMAND:
                return self.respond_to_list_keywords_command()
            case self.ADD_KEYWORD_COMMAND:
                return self.respond_to_add_keyword_command()
            case self.REMOVE_KEYWORD_COMMAND:
                return self.respond_to_remove_keyword_command()
            case self.SET_SCORE_COMMAND:
                return self.respond_to_set_score_command()
            case self.STOP_COMMAND:
                return self.respond_to_stop_command()
            case self.SUBSCRIBE_COMMAND:
                return self.respond_to_subscribe_command()
            case self.UNSUBSCRIBE_COMMAND:
                return self.respond_to_unsubscribe_command()
            case self.LIST_SUBSCRIPTIONS_COMMAND:
                return self.respond_to_list_subscriptions_command()
            case self.FOLLOW_COMMAND:
                return self.respond_to_follow_command()
            case self.UNFOLLOW_COMMAND:
                return self.respond_to_unfollow_command()
            case self.DOMAINS_COMMAND:
                return self.respond_to_domains_command()
            case _:
                return self.respond_to_undefined_command()

    def check_user_message(self) -> str:  # type: ignore[return]
        match self.telegram_update.text.split():
            case ["/start"]:
                return self.START_COMMAND
            case ["/help"]:
                return self.HELP_COMMAND
            case ["/keywords"]:
                return self.LIST_KEYWORDS_COMMAND
            case ["/add", _, *_]:
                return self.ADD_KEYWORD_COMMAND
            case ["/remove", _, *_]:
                return self.REMOVE_KEYWORD_COMMAND
            case ["/set_score", score] if score.isnumeric():  # type: ignore
                return self.SET_SCORE_COMMAND
            case ["/stop"]:
                return self.STOP_COMMAND
            case ["/subscribe", thread_id] if thread_id.isnumeric():  # type: ignore
                return self.SUBSCRIBE_COMMAND
            case ["/unsubscribe", thread_id] if thread_id.isnumeric():  # type: ignore
                return self.UNSUBSCRIBE_COMMAND
            case ["/subscriptions"]:
                return self.LIST_SUBSCRIPTIONS_COMMAND
            case ["/follow", _]:
                return self.FOLLOW_COMMAND
            case ["/unfollow", _]:
                return self.UNFOLLOW_COMMAND
            case ["/domains"]:
                return self.DOMAINS_COMMAND
            case _:
                return self.UNDEFINED_COMMAND

    def respond_to_start_and_help_command(self) -> str:
        return (
            "This is [HackerNews](https://news.ycombinator.com/) Alerts Bot 🤖\n\n"
            "Repository: https://github\\.com/lawxls/HackerNews\\-Alerts\\-Bot\n\n"
            "🔻 *FEATURES*:\n\n"
            "● *Keyword alerts*\n\n"
            "Create personal feed of stories or monitor mentions "
            "of your brand, projects or topics you're interested in\\.\n\n"
            "To set up monitoring of story titles and comment bodies, "
            "simply add keyword via `/add` command: `/add python`\n\n"
            "To monitor story titles only, use `-stories` option: `/add python \\-stories`\n\n"
            "In addition, the `/set_score` command can be used to receive stories only if they meet "
            "a specified score threshold \\(set to 1 by default\\)\\.\n\n"
            "Keyword search implemented via case\\-insensitive containment test\\.\n\n\n"
            "● *Subscribe to a thread*\n\n"
            "Monitor new comments of a thread\\.\n\n"
            "Subscribe to a thread by id: `/subscribe 34971530`\n\n\n"
            "🔻 *COMMANDS*\n\n"
            "*Keyword alerts commands*\n\n"
            "● *Add keyword*\n\n"
            "   `/add KEYWORD [\\-whole\\-word, \\-stories, \\-comments]`\n\n"
            "   If no options are specified, the bot will monitor both story titles and comment bodies\\.\n\n"
            "   Options:\n"
            "       ○ `\\-whole\\-word`\n"
            "         match whole word\n\n"
            "       ○ `\\-stories`\n"
            "         only monitor thread titles\n\n"
            "       ○ `\\-comments`\n"
            "         only monitor comment bodies\n\n"
            "   Examples:\n"
            "       ○ `/add project\\-name`\n"
            "       ○ `/add python \\-stories`\n"
            "       ○ `/add AI \\-whole\\-word \\-stories`\n"
            "       ○ `/add machine learning \\-stories`\n\n\n"
            "● *Set score threshold*\n\n"
            "   `/set\\_score SCORE`\n\n"
            "   Receive stories only if they meet a specified score threshold \\(set to 1 by default\\)\\.\n\n\n"
            "● *List keywords*\n\n"
            "   `/keywords`\n\n\n"
            "● *Remove keyword*\n\n"
            "   `/remove KEYWORD`\n\n\n"
            "*Subscribe to a thread commands*\n\n"
            "● *Subscribe to a thread*\n\n"
            "   `/subscribe ID`\n\n\n"
            "● *List subscriptions*\n\n"
            "   `/subscriptions`\n\n\n"
            "● *Unsubscribe from a thread*\n\n"
            "   `/unsubscribe ID`\n\n\n"
            "*Stories by domain names commands*\n\n"
            "● *Follow a domain name*\n\n"
            "   `/follow DOMAIN NAME`\n\n\n"
            "● *List domain names*\n\n"
            "   `/domains`\n\n\n"
            "● *Unfollow a domain name*\n\n"
            "   `/unfollow DOMAIN NAME`\n\n\n"
            "*General commands*\n\n"
            "● *Commands and other info*\n\n"
            "   `/help`\n\n\n"
            "● *Stop the bot and delete your data*\n\n"
            "   `/stop`\n\n"
        )

    def respond_to_list_keywords_command(self) -> str:
        if self.user_feed.keywords.count() == 0:
            return "Fail! Add keyword first. /help for info"

        return get_keywords_str(self.user_feed)

    def respond_to_add_keyword_command(self) -> str:
        # sourcery skip: class-extract-method

        command_data = self.telegram_update.text.replace("/add", "").strip().split(" -")
        keyword = command_data[0]
        options = command_data[1:]

        if len(keyword) > 100:
            return "Fail! Max keyword length is 100 characters"

        if len(keyword) < 2:
            return "Fail! Keyword must be at least 2 characters long"

        if self.user_feed.keywords.count() == 50:
            return "Fail! You have reached the limit of 50 keywords"

        if keyword in self.user_feed.keywords.values_list("name", flat=True):
            return "Fail! Keyword already exists"

        try:
            keyword_data = validate_and_add_options_data_to_keyword(
                keyword_data=KeywordData(user_feed=self.user_feed, name=keyword), options=options
            )
        except BadOptionCombinationError as e:
            options_str = ", ".join(e)
            return f"Fail! These options cannot be used together: {options_str}"
        except InvalidOptionError as e:
            return f"Fail! Invalid option: {e}"

        Keyword.objects.create(**asdict(keyword_data))

        if self.user_feed.keywords.count() == 1:
            return "Success! Keyword added. " "You will receive a message when this keyword is mentioned on Hacker News"

        keywords_str = get_keywords_str(self.user_feed)
        return f"Success! Keyword added. Current keywords list:\n\n{keywords_str}"

    def respond_to_remove_keyword_command(self) -> str:
        keyword = self.telegram_update.text.replace("/remove", "").strip()

        if self.user_feed.keywords.count() == 0:
            return "Fail! Add keyword first. /help for info"

        if keyword not in self.user_feed.keywords.values_list("name", flat=True):
            return "Fail! Keyword not found"

        keyword = Keyword.objects.get(user_feed=self.user_feed, name=keyword)
        keyword.delete()

        if self.user_feed.keywords.count() == 0:
            return "Success! Last keyword removed"

        keywords_str = get_keywords_str(self.user_feed)
        return f"Success! Keyword removed. Current keywords list:\n\n{keywords_str}"

    def respond_to_set_score_command(self) -> str:
        command_data = [w.strip() for w in self.telegram_update.text.split()]
        score = int(command_data[1])

        self.user_feed.score_threshold = score
        self.user_feed.save(update_fields=["score_threshold"])

        return f"Success! Score threshold set to {score}"

    def respond_to_stop_command(self) -> str:
        self.user_feed.delete()
        return "Success! Data is erased"

    def respond_to_subscribe_command(self) -> str:
        command_data = [w.strip() for w in self.telegram_update.text.split()]
        thread_id = int(command_data[1])

        thread = Thread.objects.filter(thread_id=thread_id).first()
        if not thread:
            return f"Fail! Thread with {thread_id} id not found"

        if self.user_feed.subscription_threads.count() >= 1:
            return "Fail! You can only subscribe to one thread at a time"

        self.user_feed.subscription_threads.add(thread.id)

        comment_ids_by_thread = Comment.objects.filter(thread_id_int=thread_id).values_list("id", flat=True)
        self.user_feed.subscription_comments.add(*comment_ids_by_thread)

        return f"Success! You are now subscribed to a thread: {thread.title}"

    def respond_to_unsubscribe_command(self) -> str:
        command_data = [w.strip() for w in self.telegram_update.text.split()]
        thread_id = int(command_data[1])

        thread = Thread.objects.filter(thread_id=thread_id).first()
        if not thread:
            return f"Fail! Thread with {thread_id} id not found"

        if thread not in self.user_feed.subscription_threads.all():
            return f"Fail! You are not subscribed to thread with {thread.thread_id} id"

        self.user_feed.subscription_threads.remove(thread.id)

        return f"Success! You are unsubscribed from a thread: {thread.title}"

    def respond_to_list_subscriptions_command(self) -> str:
        # refactor if users will be allowed to subscribe to multiple threads

        if self.user_feed.subscription_threads.exists() is False:
            return "You are currently not subscribed to a thread"

        thread = self.user_feed.subscription_threads.all()[0]

        return f"You are subscribed to a thread: {thread.title}\nThread id: {thread.thread_id}"

    def respond_to_follow_command(self) -> str:
        command_data = [w.strip() for w in self.telegram_update.text.split()]
        domain_name = command_data[1]

        if len(domain_name) > 243:
            return "Fail! Maximum length of a domain name is 243 characters"

        if len(domain_name) < 3:
            return "Fail! Minimum length of a domain name is 3 characters"

        if len(self.user_feed.domain_names) >= 5:
            return "Fail! You are following maximum amount of domain names (5)"

        if domain_name in self.user_feed.domain_names:
            return f"Fail! You are already following {domain_name}"

        self.user_feed.domain_names.append(domain_name)
        self.user_feed.save()

        return f"Success! You are now following {domain_name}"

    def respond_to_unfollow_command(self) -> str:
        command_data = [w.strip() for w in self.telegram_update.text.split()]
        domain_name = command_data[1]

        if domain_name not in self.user_feed.domain_names:
            return f"Fail! You are not following {domain_name}"

        self.user_feed.domain_names.remove(domain_name)
        self.user_feed.save()

        return f"Success! Unfollowed {domain_name}"

    def respond_to_domains_command(self) -> str:
        return (
            "\n".join(self.user_feed.domain_names)
            if self.user_feed.domain_names
            else "You are not following any domain name"
        )

    def respond_to_undefined_command(self) -> str:
        return "Huh? Use /help to see the list of implemented commands"


class SendAlertsService:
    def __init__(self, user_feed: UserFeed):
        self.user_feed = user_feed

    def find_new_stories_by_domain_names(self) -> QuerySet[Thread]:
        domain_names = self.user_feed.domain_names

        date_from = timezone.now() - datetime.timedelta(days=1)
        threads_from_24_hours = Thread.objects.filter(created__gte=date_from)

        threads_by_domain_names = Thread.objects.none()

        for domain_name in domain_names:
            threads_by_domain_name = threads_from_24_hours.filter(
                link__icontains=domain_name,
                score__gte=self.user_feed.score_threshold,
            )
            threads_by_domain_names = threads_by_domain_names | threads_by_domain_name

        return threads_by_domain_names.difference(self.user_feed.threads.all())

    def send_subscription_comments_to_telegram_feed(self):
        # refactor if users will be allowed to subscribe to multiple threads
        send_message_request = SendMessageRequest()

        subscribed_thread = self.user_feed.subscription_threads.all()[0]
        subscribed_thread_comments = Comment.objects.filter(thread_id_int=subscribed_thread.thread_id)

        new_comments = subscribed_thread_comments.difference(self.user_feed.subscription_comments.all())

        messages_sent: list[bool] = []
        for comment in new_comments:
            sleep(0.02)

            comment_created_at_str = comment.comment_created_at.strftime("%B %d, %H:%M")

            text = (
                f"Subscribed thread: {subscribed_thread.title}\n"
                f"By {comment.username} on {comment_created_at_str}\n\n"
                f"{comment.body}"
            )

            reply_button = InlineKeyboardButton(
                text="reply", url=f"{settings.HACKERNEWS_URL}reply?id={comment.comment_id}"
            )
            context_button = InlineKeyboardButton(
                text="context",
                url=(f"{settings.HACKERNEWS_URL}item?id=" f"{comment.thread_id_int}#{comment.comment_id}"),
            )

            inline_keyboard_markup = {"inline_keyboard": [[reply_button, context_button]]}

            sent = send_message_request.send_message(
                chat_id=self.user_feed.chat_id,
                text=text,
                inline_keyboard_markup=inline_keyboard_markup,
                parse_mode=None,
            )
            messages_sent.append(sent)

            self.user_feed.subscription_comments.add(comment)

        return all(messages_sent)

    def send_threads_to_telegram_feed(self, threads: Iterable[Thread]) -> bool:
        send_message_request = SendMessageRequest()

        messages_sent: list[bool] = []
        for thread in threads:
            sleep(0.02)

            thread_created_at_str = thread.thread_created_at.strftime("%B %d, %H:%M")
            escaped_title = escape_markdown(text=thread.title, version=2)
            escaped_story_link = escape_markdown(text=thread.link, version=2, entity_type="text_link")
            escaped_comments_link = escape_markdown(
                text=thread.comments_link, version=2, entity_type="text_link"  # type: ignore
            )
            text = (
                f"[*{escaped_title}*]({escaped_story_link}) \n\n"
                f"{thread.score}\\+ points \\| [{thread.comments_count}\\+ "
                f"comments]({escaped_comments_link}) \\| {thread_created_at_str}"
            )

            read_button = InlineKeyboardButton(text="read", url=thread.link)
            comments_button = InlineKeyboardButton(text=f"{thread.comments_count}+ comments", url=thread.comments_link)

            inline_keyboard_markup = {"inline_keyboard": [[read_button, comments_button]]}

            sent = send_message_request.send_message(
                chat_id=self.user_feed.chat_id,
                text=text,
                inline_keyboard_markup=inline_keyboard_markup,
                parse_mode="MarkdownV2",
            )
            messages_sent.append(sent)

        return all(messages_sent)

    def send_comments_to_telegram_feed(self, comments_by_keywords: Mapping[str, Iterable[Comment]]) -> bool:
        send_message_request = SendMessageRequest()

        messages_sent: list[bool] = []
        for keyword in comments_by_keywords:
            for comment in comments_by_keywords[keyword]:
                sleep(0.02)

                comment_created_at_str = comment.comment_created_at.strftime("%B %d, %H:%M")

                text = (
                    f"Keyword match: {keyword}\n"
                    f"By {comment.username} on {comment_created_at_str}\n\n"
                    f"{comment.body}"
                )

                reply_button = InlineKeyboardButton(
                    text="reply", url=f"{settings.HACKERNEWS_URL}reply?id={comment.comment_id}"
                )
                context_button = InlineKeyboardButton(
                    text="context",
                    url=(f"{settings.HACKERNEWS_URL}item?id=" f"{comment.thread_id_int}#{comment.comment_id}"),
                )

                inline_keyboard_markup = {"inline_keyboard": [[reply_button, context_button]]}

                sent = send_message_request.send_message(
                    chat_id=self.user_feed.chat_id,
                    text=text,
                    inline_keyboard_markup=inline_keyboard_markup,
                    parse_mode=None,
                )
                messages_sent.append(sent)

        return all(messages_sent)

    def find_new_threads_by_keywords(self) -> QuerySet[Thread]:
        keywords = self.user_feed.keywords.filter(search_threads=True)

        date_from = timezone.now() - datetime.timedelta(days=1)
        threads_from_24_hours = Thread.objects.filter(created__gte=date_from)

        threads_by_keywords = Thread.objects.none()

        for keyword in keywords:
            keyword_name = keyword.name
            if keyword.is_full_match is True:
                keyword_name = f" {keyword_name} "

            threads_by_keyword = threads_from_24_hours.filter(
                title__icontains=keyword_name,
                score__gte=self.user_feed.score_threshold,
                comments_link__isnull=False,  # exclude YC hiring posts
            )
            threads_by_keywords = threads_by_keywords | threads_by_keyword

        return threads_by_keywords.difference(self.user_feed.threads.all())

    def find_new_comments_by_keywords(
        self,
    ) -> tuple[QuerySet[Comment], Mapping[str, QuerySet[Comment]]]:
        keywords = self.user_feed.keywords.filter(search_comments=True)

        date_from = timezone.now() - datetime.timedelta(days=1)
        comments_from_24_hours = Comment.objects.filter(created__gte=date_from)

        comments_by_keywords = Comment.objects.none()
        comments_by_keywords_dict: dict[str, QuerySet[Comment]] = {}

        for keyword in keywords:
            if keyword.is_full_match is False:
                comments_by_keyword = comments_from_24_hours.filter(
                    body__icontains=keyword.name,
                )
            else:
                comments_by_keyword = comments_from_24_hours.filter(
                    body__icontains=f" {keyword.name} ",
                )

            comments_by_keywords_dict[keyword.name] = comments_by_keyword
            comments_by_keywords = comments_by_keywords | comments_by_keyword

        all_comments = self.user_feed.comments.all()
        new_comments = comments_by_keywords.difference(all_comments)
        for k, v in comments_by_keywords_dict.items():
            comments_by_keywords_dict[k] = v.difference(all_comments)

        return new_comments, comments_by_keywords_dict


def validate_and_add_options_data_to_keyword(keyword_data: KeywordData, options: list[str]) -> KeywordData:
    if "stories" in options and "comments" in options:
        raise BadOptionCombinationError(options=["-stories", "-comments"])

    for option in options:
        match option:
            case "whole-word":
                keyword_data.is_full_match = True
            case "stories":
                keyword_data.search_comments = False
            case "comments":
                keyword_data.search_threads = False
            case _:
                raise InvalidOptionError(option=option)

    return keyword_data


def get_keywords_str(user_feed: UserFeed) -> str:
    """Get list of keywords and it's options as formatted string"""

    keyword_lines = []
    for keyword in user_feed.keywords.all():
        options = []
        if keyword.search_comments is False:
            options.append("stories")
        if keyword.search_threads is False:
            options.append("comments")
        if keyword.is_full_match is True:
            options.append("whole-word")

        options_str = ", ".join(options)
        keyword_line = f"Keyword: {keyword.name}\n" f"Options: {options_str}\n\n"
        keyword_lines.append(keyword_line)

    return "\n".join(keyword_lines)
