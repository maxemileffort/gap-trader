from dotenv import load_dotenv
import os
load_dotenv()

APCA_API_KEY_ID=os.getenv("APCA_API_KEY_ID")
APCA_API_SECRET_KEY=os.getenv("APCA_API_SECRET_KEY")
APCA_API_BASE_URL=os.getenv("APCA_API_BASE_URL")
APCA_API_PAPER_BASE_URL=os.getenv("APCA_API_PAPER_BASE_URL")
CHROMEDRIVER_DIR=os.getenv("CHROMEDRIVER_DIR")


