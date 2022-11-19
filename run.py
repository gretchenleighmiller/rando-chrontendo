import cv2
import os
from random import randint
import twitter
from cohost.models.user import User as CohostUser
from cohost.models.block import AttachmentBlock as CohostAttachmentBlock

videos_directory = os.environ["VIDEOS_DIR"]

twitter_consumer_key = os.environ["TWITTER_CONSUMER_KEY"]
twitter_consumer_secret = os.environ["TWITTER_CONSUMER_SECRET"]
twitter_access_token_key = os.environ["TWITTER_ACCESS_TOKEN_KEY"]
twitter_access_token_secret = os.environ["TWITTER_ACCESS_TOKEN_SECRET"]

cohost_email = os.environ["COHOST_EMAIL"]
cohost_password = os.environ["COHOST_PASSWORD"]


def run():
    video_files = os.listdir(videos_directory)
    file_to_grab = randint(0, len(video_files) - 1)
    file_name = video_files[file_to_grab]

    vid = cv2.VideoCapture("{}/{}".format(videos_directory, file_name))

    total_frames = vid.get(cv2.CAP_PROP_FRAME_COUNT)
    frame_to_grab = randint(200, total_frames - 200)
    vid.set(cv2.CAP_PROP_POS_FRAMES, frame_to_grab)

    ret, curframe = vid.read()
    cv2.imwrite("image.jpg", curframe)
    vid.release()
    cv2.destroyAllWindows()

    post_twitter()
    post_cohost()


def post_twitter():
    api = twitter.Api(
        consumer_key=twitter_consumer_key,
        consumer_secret=twitter_consumer_secret,
        access_token_key=twitter_access_token_key,
        access_token_secret=twitter_access_token_secret,
        sleep_on_rate_limit=True,
    )

    api.PostUpdate(status="", media="image.jpg")


def post_cohost():
    user = CohostUser.login(cohost_email, cohost_password)
    project = user.getProject("randochrontendo")

    blocks = [CohostAttachmentBlock("image.jpg")]
    project.post("", blocks)


if __name__ == "__main__":
    run()
