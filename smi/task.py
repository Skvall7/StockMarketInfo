from config.app import taskiq_broker
from smi.producer import collect_all_symbols, collect_binance_rates, collect_garantex_rates, collect_payeer_rates, \
    collect_htx_rates, collect_cbr_rates, collect_wmg_rates

# Определение задач с расписанием
# taskiq_broker.task(
#     message=collect_all_symbols,
#     topic='empty',
#     schedule=[{
#         "cron": "* * * * *",
#     }],
# )
#
# taskiq_broker.task(
#     key='fdf',
#     message=collect_binance_rates,
#     topic="empty",
#     schedule=[{
#         "cron": "* * * * *",
#     }],
# )
#
# taskiq_broker.task(
#     key='fdf',
#     message=collect_garantex_rates,
#     topic="empty",
#     schedule=[{
#         "cron": "* * * * *",
#     }],
# )
#
# taskiq_broker.task(
#     key='fdf',
#     message=collect_payeer_rates,
#     topic="empty",
#     schedule=[{
#         "cron": "* * * * *",
#     }],
# )
#
# taskiq_broker.task(
#     key='fdf',
#     message=collect_htx_rates,
#     topic="empty",
#     schedule=[{
#         "cron": "* * * * *",
#     }],
# )
#
# taskiq_broker.task(
#     key='fdf',
#     message=collect_cbr_rates,
#     topic="empty",
#     schedule=[{
#         "cron": "* * * * *",
#     }],
# )
#
# taskiq_broker.task(
#     key='fdf',
#     message=collect_wmg_rates,
#     topic="empty",
#     schedule=[{
#         "cron": "* * * * *",
#     }],
# )


def register_task(message, cron_schedule):
    taskiq_broker.task(
        key=message.__name__,
        message=message,
        topic="empty",
        schedule=[cron_schedule],
    )


register_task(collect_all_symbols, {"cron": "* * * * *"})
register_task(collect_binance_rates, {"cron": "* * * * *"})
register_task(collect_garantex_rates, {"cron": "* * * * *"})
register_task(collect_payeer_rates, {"cron": "* * * * *"})
register_task(collect_htx_rates, {"cron": "* * * * *"})
register_task(collect_cbr_rates, {"cron": "* * * * *"})
register_task(collect_wmg_rates, {"cron": "* * * * *"})
