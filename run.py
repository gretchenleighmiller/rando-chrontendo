import logging
import math
import os
import time
from random import randint

import cv2
import pytumblr
from cohost.models.block import AttachmentBlock as CohostAttachmentBlock
from cohost.models.user import User as CohostUser
from mastodon import Mastodon
import tweepy

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
fh = logging.FileHandler("randochrontendo.log")
fh.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)


VIDEOS_DIRECTORY = os.environ.get("VIDEOS_DIR")

TWITTER_CREDENTIALS = {
    "access_token": os.environ.get("TWITTER_ACCESS_TOKEN_KEY"),
    "access_token_secret": os.environ.get("TWITTER_ACCESS_TOKEN_SECRET"),
    "consumer_key": os.environ.get("TWITTER_CONSUMER_KEY"),
    "consumer_secret": os.environ.get("TWITTER_CONSUMER_SECRET"),
}
COHOST_CREDENTIALS = {
    "email": os.environ.get("COHOST_EMAIL"),
    "password": os.environ.get("COHOST_PASSWORD"),
}
COHOST_PROJECT = os.environ.get("COHOST_PROJECT")
MASTODON_CREDENTIALS = {
    "access_token": os.environ.get("MASTODON_ACCESS_TOKEN"),
    "api_base_url": os.environ.get("MASTODON_API_BASE_URL"),
}
TUMBLR_CREDENTIALS = {
    "consumer_key": os.environ.get("TUMBLR_CONSUMER_KEY"),
    "consumer_secret": os.environ.get("TUMBLR_CONSUMER_SECRET"),
    "oauth_token": os.environ.get("TUMBLR_OAUTH_TOKEN"),
    "oauth_secret": os.environ.get("TUMBLR_OAUTH_SECRET"),
}
TUMBLR_BLOG = os.environ.get("TUMBLR_BLOG")


def run():
    post = RandoChrontendoPost()

    try:
        post.post_twitter()
    except Exception as e:
        logger.error(f"Twitter post failed: {e}")

    try:
        post.post_cohost()
    except Exception as e:
        logger.error(f"Cohost post failed: {e}")

    try:
        post.post_tumblr()
    except Exception as e:
        logger.error(f"Tumblr post failed: {e}")

    try:
        post.post_mastodon()
    except Exception as e:
        logger.error(f"Mastodon post failed: {e}")


class RandoChrontendoPost:
    def __init__(self, image_file_name="image.jpg"):
        self.image_file_name = image_file_name
        self._get_video_file()
        self._write_image()

    @property
    def alt_text(self):
        return f"{self.video_name} ({self.timestamp})"

    def post_twitter(self):
        media_upload_auth = tweepy.OAuth1UserHandler(**TWITTER_CREDENTIALS)
        media_upload_api = tweepy.API(media_upload_auth)
        with open(self.image_file_name, "rb") as image_data:
            media_id = media_upload_api.media_upload(self.image_file_name, file=image_data).media_id_string
        media_upload_api.create_media_metadata(media_id, self.alt_text)

        twitter_v2_client = tweepy.Client(**TWITTER_CREDENTIALS)
        twitter_v2_client.create_tweet(media_ids=[media_id])

    def post_cohost(self):
        user = CohostUser.login(**COHOST_CREDENTIALS)
        project = user.getProject(COHOST_PROJECT)
        blocks = [CohostAttachmentBlock(self.image_file_name, alt_text=self.alt_text)]
        project.post("", blocks)

    def post_tumblr(self):
        client = pytumblr.TumblrRestClient(**TUMBLR_CREDENTIALS)
        client.create_photo(
            TUMBLR_BLOG,
            data=self.image_file_name,
            caption=self.alt_text,
        )

    def post_mastodon(self):
        mastodon = Mastodon(**MASTODON_CREDENTIALS)
        media = mastodon.media_post(self.image_file_name, description=self.alt_text)
        timeout = 1
        while media["url"] is None:
            time.sleep(timeout)
            media = mastodon.media(media)
            timeout *= 2
        mastodon.status_post("", media_ids=[media["id"]])

    def _get_video_file(self):
        video_files = os.listdir(VIDEOS_DIRECTORY)
        file_to_grab = randint(0, len(video_files) - 1)
        self.file_name = video_files[file_to_grab]
        self.video_name = (self.file_name.split(".")[0]).strip()

    def _write_image(self):
        video = cv2.VideoCapture("{}/{}".format(VIDEOS_DIRECTORY, self.file_name))
        total_frames = video.get(cv2.CAP_PROP_FRAME_COUNT)

        count_non_zero = 0
        while count_non_zero <= 2500:
            frame_to_grab = randint(1, total_frames)
            video.set(cv2.CAP_PROP_POS_FRAMES, frame_to_grab)
            _, curframe = video.read()
            cv2.imwrite(self.image_file_name, curframe)
            img = cv2.imread(self.image_file_name, 0)
            count_non_zero = cv2.countNonZero(img)

        self._set_timestamp(video.get(cv2.CAP_PROP_POS_MSEC))

        video.release()
        cv2.destroyAllWindows()

    def _set_timestamp(self, milliseconds):
        seconds = math.floor((milliseconds / 1000) % 60)
        minutes = math.floor((milliseconds / (1000 * 60)) % 60)
        hours = math.floor((milliseconds / (1000 * 60 * 60)) % 24)
        self.timestamp = f"{hours:02}:{minutes:02}:{seconds:02}"


if __name__ == "__main__":
    run()
