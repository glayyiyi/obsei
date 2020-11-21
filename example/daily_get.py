import logging
import os
import sys
from pathlib import Path

from obsei.sink.dailyget_sink import DailyGetSink, DailyGetSinkConfig
from obsei.source.twitter_source import TwitterSource, TwitterSourceConfig
from obsei.text_analyzer import AnalyzerConfig, TextAnalyzer

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

sink_config = DailyGetSinkConfig(
    url=os.environ['DAILYGET_URL'],
    partner_id=os.environ['DAILYGET_PARTNER_ID'],
    consumer_phone_number=os.environ['DAILYGET_CONSUMER_NUMBER'],
    source_information="Twitter " + os.environ['DAILYGET_QUERY'],
    base_payload={
        "partnerId": os.environ['DAILYGET_PARTNER_ID'],
        "consumerPhoneNumber": os.environ['DAILYGET_CONSUMER_NUMBER'],
    }
)

dir_path = Path(__file__).resolve().parent.parent
source_config = TwitterSourceConfig(
    twitter_config_filename=f'{dir_path}/config/twitter.yaml',
    keywords=[os.environ['DAILYGET_QUERY']],
    lookup_period=os.environ['DAILYGET_LOOKUP_PERIOD'],
    tweet_fields=["author_id", "conversation_id", "created_at", "id", "public_metrics", "text"],
    user_fields=["id", "name", "public_metrics", "username", "verified"],
    expansions=["author_id"],
    place_fields=None,
    max_tweets=10,
)

source = TwitterSource()
sink = DailyGetSink()
text_analyzer = TextAnalyzer(
    model_name_or_path="joeddav/bart-large-mnli-yahoo-answers",
 #   model_name_or_path="joeddav/xlm-roberta-large-xnli",
    initialize_model=True,
    analyzer_config=AnalyzerConfig(
        labels=["service", "delay", "tracking", "no response", "missing items", "delivery", "mask"],
        use_sentiment_model=True
    )
)

source_response_list = source.lookup(source_config)
for idx, source_response in enumerate(source_response_list):
    logger.info(f"source_response#'{idx}'='{source_response.__dict__}'")

analyzer_response_list = text_analyzer.analyze_input(
    source_response_list=source_response_list
)
for idx, an_response in enumerate(analyzer_response_list):
    logger.info(f"analyzer_response#'{idx}'='{an_response.__dict__}'")

# HTTP Sink
sink_response_list = sink.send_data(analyzer_response_list, sink_config)
for sink_response in sink_response_list:
    if sink_response is not None:
        logger.info(f"sink_response='{sink_response.__dict__}'")
