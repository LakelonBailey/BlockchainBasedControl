# <your_app>/management/commands/seed_data.py

import random
import uuid
import secrets
from decimal import Decimal
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone
from oauth2_provider.models import Application

from api.models import SmartMeter, BCOrder, BCTransaction


class Command(BaseCommand):
    help = "Seed the DB with SmartMeters, BCOrders, and BCTransactions (with realistic timestamps)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--meters",
            type=int,
            default=50,
            help="How many SmartMeters to create",
        )
        parser.add_argument(
            "--orders-per-meter",
            type=int,
            default=20,
            help="How many BCOrders per SmartMeter",
        )
        parser.add_argument(
            "--max-transactions",
            type=int,
            default=5,
            help="Max BCTransactions per order",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        num_meters = options["meters"]
        orders_per_meter = options["orders_per_meter"]
        max_tx = options["max_transactions"]

        self.stdout.write(f"🕹️  Creating {num_meters} SmartMeters…")
        smart_meters = []
        for _ in range(num_meters):
            secret = secrets.token_urlsafe(32)
            app = Application.objects.create(
                name=f"SeedMeter {uuid.uuid4()}",
                client_type=Application.CLIENT_CONFIDENTIAL,
                client_secret=secret,
                authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            )
            sm = SmartMeter.objects.create(
                application=app,
                raw_client_secret=secret,
            )
            smart_meters.append(sm)

        self.stdout.write("📦 Creating BCOrders…")
        orders = []
        for sm in smart_meters:
            for _ in range(orders_per_meter):
                total_amount = Decimal(str(random.uniform(1e-7, 4))).quantize(
                    Decimal("0.00000001")
                )
                order_type = random.choice(["buy", "sell"])
                order = BCOrder.objects.create(
                    order_id=str(uuid.uuid4()),
                    smart_meter=sm,
                    order_type=order_type,
                    state="placed",
                    total_amount=total_amount,
                    filled_amount=Decimal("0"),
                    is_partial=True,
                )
                orders.append(order)

        # Assign each order a random created_at within the last 30 days
        self.stdout.write("⏱️  Randomizing order timestamps…")
        for order in orders:
            random_secs = random.uniform(0, 30 * 24 * 3600)
            order.created_at = now - timedelta(seconds=random_secs)
        BCOrder.objects.bulk_update(orders, ["created_at"])

        self.stdout.write("🚀 Generating BCTransactions (bulk)…")
        tx_list = []
        for order in orders:
            order_time = order.created_at
            num_tx = random.randint(1, max_tx)
            for _ in range(num_tx):
                amt = Decimal(
                    str(random.uniform(1e-7, float(order.total_amount)))
                ).quantize(Decimal("0.00000001"))
                price = Decimal(str(random.uniform(0.01, 1))).quantize(
                    Decimal("0.00000001")
                )
                # pick a timestamp between order_time and now
                span = (now - order_time).total_seconds()
                tx_time = order_time + timedelta(seconds=random.uniform(0, span))

                tx_list.append(
                    BCTransaction(
                        order=order,
                        amount=amt,
                        transaction_type=(
                            "buy" if order.order_type == "sell" else "sell"
                        ),
                        executed_price=price,
                        created_at=tx_time,
                    )
                )

        BCTransaction.objects.bulk_create(tx_list)

        self.stdout.write("🔄 Updating BCOrders with filled_amount & state…")
        # Sum up all tx amounts per order
        sums = BCTransaction.objects.values("order").annotate(filled=Sum("amount"))
        filled_map = {item["order"]: item["filled"] for item in sums}

        to_update = []
        for order in orders:
            filled = filled_map.get(order.uuid, Decimal("0"))
            order.filled_amount = filled
            if filled >= order.total_amount:
                order.is_partial = False
                order.state = "matched"
            else:
                order.is_partial = True
                order.state = "placed"
            to_update.append(order)

        BCOrder.objects.bulk_update(to_update, ["filled_amount", "is_partial", "state"])

        self.stdout.write(self.style.SUCCESS("🎉 Seeding complete!"))
