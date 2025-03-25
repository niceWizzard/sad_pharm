import datetime
import uuid
from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import CategoryType, InventoryItem, InventoryStock, InventoryTransaction, PackagingType, StockRecord, SubcategoryType, UnitType
from django.db.models import Sum
from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_item():
    return InventoryItem.objects.create(
        id=str(uuid.uuid4()),  # Ensure a valid UUID
        category=CategoryType.ANTACIDS,
        subcategory=SubcategoryType.ANTACID,
        item_name="Magnesium Hydroxide",
        brand_name="Phillips' Milk of Magnesia",
        generic_name="Magnesium Hydroxide",
        dosage_form="Liquid",
        strength_per_size="400mg/5ml",
        packaging=PackagingType.BOTTLE,
        quantity=120,
        unit_size=UnitType.ML,
    )

def create_test_stock(item : InventoryItem):
    return InventoryStock.objects.create(
        item=item,
        quantity=5,
        expiration_date=datetime.date.today(),
        date_of_delivery=datetime.date.today(),
    )

class ItemTestCase(TestCase):
    def setUp(self):
        """Set up an inventory item for testing"""
        self.item = create_test_item()
        self.stock = create_test_stock(self.item)
        self.user = User.objects.create_user(
            email="test_email@example.com",
            password="1234"
        )


    def test_item_exists(self):
        """Test if an item exists in the database"""
        item = InventoryItem.objects.get(item_name="Magnesium Hydroxide")
        self.assertIsNotNone(item)

    def test_default_stock_value(self):
        """Ensure stocks are initialized correctly"""
        self.assertEqual(self.stock.quantity, 5)
    
    def test_invalid_unit_type_raise_error(self):
        with self.assertRaises(ValidationError):
            InventoryItem.objects.create(
                category=CategoryType.ANTACIDS,
                subcategory=SubcategoryType.ANTACID,
                item_name="Magnesium Hydroxide",
                brand_name="Phillips' Milk of Magnesia",
                generic_name="Magnesium Hydroxide",
                dosage_form="Liquid",
                strength_per_size="400mg/5ml",
                packaging=PackagingType.BOTTLE,
                quantity=120,
                unit_size="lkjsdf",
            )

    def test_invalid_category_type_raise_error(self):
        with self.assertRaises(ValidationError):
            InventoryItem.objects.create(
                category="SOME INVALID CATEOGRY",
                subcategory=SubcategoryType.ANTACID,
                item_name="Magnesium Hydroxide",
                brand_name="Phillips' Milk of Magnesia",
                generic_name="Magnesium Hydroxide",
                dosage_form="Liquid",
                strength_per_size="400mg/5ml",
                packaging=PackagingType.BOTTLE,
                quantity=120,
                unit_size=UnitType.EACH,  
            )
    def test_invalid_subcategory_type_raise_error(self):
        with self.assertRaises(ValidationError):
            InventoryItem.objects.create(
                category=CategoryType.ANTACIDS,
                subcategory="SOME INVALID SUBCATEGORY",
                item_name="Magnesium Hydroxide",
                brand_name="Phillips' Milk of Magnesia",
                generic_name="Magnesium Hydroxide",
                dosage_form="Liquid",
                strength_per_size="400mg/5ml",
                packaging="Bottle",
                quantity=120,
                unit_size=UnitType.EACH,  
            )

    def test_invalid_packaging_type_raise_error(self):
        with self.assertRaises(ValidationError):
            InventoryItem.objects.create(
                category="SOME INVALID CATEOGRY",
                subcategory=SubcategoryType.ANTACID,
                item_name="Magnesium Hydroxide",
                brand_name="Phillips' Milk of Magnesia",
                generic_name="Magnesium Hydroxide",
                dosage_form="Liquid",
                strength_per_size="400mg/5ml",
                packaging="INVALID LPACKAGING TYPE",
                quantity=120,
                unit_size=UnitType.EACH,  
            )

    def test_expired_stocks_are_excluded_from_transaction(self):
        expired = create_test_stock(self.item)
        expired.quantity = 100
        expired.expiration_date = datetime.date.today() - datetime.timedelta(1)
        expired.save()
        InventoryTransaction.objects.create(
            item=self.item,
            created_by=self.user,
            quantity=5,
        )
        self.assertEqual(
            InventoryStock.objects.get(id=self.stock.id).quantity,0
        )
        self.assertEqual(
            expired.quantity, 100
        )
    
    def test_stocks_property_is_accurate(self):
        self.assertEqual(
            self.item.stocks, 
            5
        )
        self.stock.quantity = 100
        self.stock.save()
        self.item.refresh_from_db()
        self.assertEqual(
            InventoryItem.objects.get(id=self.item.id).stocks, 
            100
        )
        for i in range(1,5):
            InventoryTransaction.objects.create(
               item=self.item,
                created_by=self.user,
                quantity=5,
            )
            self.assertEqual(
                InventoryItem.objects.get(id=self.item.id).stocks, 
                100 - 5*i
            )





class TransactionTestCase(TestCase):
    def setUp(self):
        """Set up an inventory item and user for transactions"""
        self.item = create_test_item()
        self.stock = create_test_stock(self.item)
        self.user = User.objects.create_user(
            email="test_email@example.com",
            password="1234"
        )

    def test_transaction_modifies_item_stock(self):
        """Test that adding stock increases the item's stock quantity"""
        InventoryTransaction.objects.create(
            item=self.item,
            created_by=self.user,
            quantity=5,
        )
        modified_stock = InventoryStock.objects.get(item=self.item)
        self.assertEqual(modified_stock.quantity, 0)

    def test_transaction_creates_stock_record(self):
        transaction = InventoryTransaction.objects.create(
            item=self.item,
            created_by=self.user,
            quantity=5,
        )
        self.assertTrue(
            StockRecord.objects.filter(
                transaction=transaction,
                stock=self.stock,
            ).exists(),
            "Didn't find any StockRecords after creating a transaction."
        )

    def test_transaction_fails_when_insufficient_stock(self):
        """Test that removing more stock than available raises an error"""
        with self.assertRaises(ValidationError) as e:
            InventoryTransaction.objects.create(
                item=self.item,
                created_by=self.user,
                quantity=5000000,
            )
            self.assertEqual(str(e.exception), "Not enough stocks to make this transaction!")

    def test_multiple_transactions_affect_stock_correctly(self):
        """Test multiple transactions updating stock properly"""
        InventoryTransaction.objects.create(
            item=self.item,
            created_by=self.user,
            quantity=2,
        )
        InventoryTransaction.objects.create(
            item=self.item,
            created_by=self.user,
            quantity=2,
        )
        modified_stock = InventoryStock.objects.get(id=self.stock.id)
        self.assertEqual(modified_stock.quantity, 1)  # 5 + 2 - 3 = 4

    def test_transaction_creates_many_stock_records(self):
        create_test_stock(self.item)
        transaction = InventoryTransaction.objects.create(
            item=self.item,
            created_by=self.user,
            quantity=6,
        )
        stock_records = StockRecord.objects.filter(transaction=transaction).order_by("quantity")
        self.assertEqual(stock_records.count(), 2, "Transaction should have created 2 stock records")
        self.assertEqual(stock_records[0].quantity, 1)
        self.assertEqual(stock_records[1].quantity, 5)

    def test_transaction_modification_changes_stock(self):
        transaction = InventoryTransaction.objects.create(
            item=self.item,
            created_by=self.user,
            quantity=2,
        )
        transaction.quantity = 5
        transaction.save()
        self.assertEqual(
            InventoryStock.objects.filter(item=self.item).aggregate(Sum('quantity'))["quantity__sum"],
            0,
        )
        
        
    def test_transaction_deletion_changes_stock(self):
        create_test_stock(self.item)
        transaction = InventoryTransaction.objects.create(
            item=self.item,
            created_by=self.user,
            quantity=9,
        )
        transaction.delete()

        modified_stock = InventoryStock.objects.filter(item=self.item).aggregate(Sum('quantity'))["quantity__sum"]
        self.assertEqual(modified_stock, 10)

    def test_item_deletion_cascades(self):
        transaction = InventoryTransaction.objects.create(
            item=self.item,
            created_by=self.user,
            quantity=2,
        )
        self.item.delete()
        self.assertEqual(
            0,
            InventoryTransaction.objects.all().count(),
        )


    def test_stock_cannot_be_negative_due_to_transactions(self):
        transaction = InventoryTransaction.objects.create(
            item=self.item,
            created_by=self.user,
            quantity=2,
        )
        transaction.quantity = 10
        with self.assertRaises(ValidationError):
            transaction.save()
            transaction.quantity = -2
            transaction.save()
    
    def test_many_transaction_is_consistent(self):
        self.stock.quantity = 1000
        self.stock.save()
        loop = 10
        for i in range(1,loop):
            InventoryTransaction.objects.create(
                item=self.item,
                created_by=self.user,
                quantity=50,
            )
            mod_stock = InventoryStock.objects.get(id=self.stock.id)
            self.assertEqual(
                mod_stock.quantity,
                self.stock.quantity - 50 * i
            )

        for transaction in InventoryTransaction.objects.filter(item=self.item):
            transaction.delete()
        self.assertEqual(
            InventoryStock.objects.get(id=self.stock.id).quantity,
            1000
        )
    
    def test_transaction_is_fifo(self):
        stock2 = create_test_stock(self.item)
        stock2.expiration_date += datetime.timedelta(1)
        stock2.save()

        InventoryTransaction.objects.create(
            item=self.item,
            created_by=self.user,
            quantity=5,
        )

        self.assertEqual(InventoryStock.objects.get(id=self.stock.id).quantity, 0)
        self.assertEqual(InventoryStock.objects.get(id=stock2.id).quantity, 5)

        InventoryTransaction.objects.create(
            item=self.item,
            created_by=self.user,
            quantity=5,
        )
        self.assertEqual(InventoryStock.objects.get(id=stock2.id).quantity, 0)



        

class InventoryStockTestCase(TestCase):
    def setUp(self):
        """Set up an inventory item for testing"""
        self.item = create_test_item()
        self.stock = create_test_stock(self.item)

    def deletion_of_item_cascades(self):
        self.assertEqual(
            InventoryStock.objects.all().count(),
            1
        )
        self.item.delete()
        self.assertEqual(
            InventoryStock.objects.all().count(),
            0
        )
    def test_cannot_add_expired_stock(self):
        """Ensure that adding stock with a past expiration date raises an error"""
        with self.assertRaises(ValidationError):
            InventoryStock.objects.create(
                item=self.item,
                expiration_date=datetime.date.today() - datetime.timedelta(days=1),
                quantity=5
            )

    def test_can_update_expired_stock(self):
        """Ensure modifying stock for an expired item is allowed"""
        self.stock.expiration_date = datetime.date.today() - datetime.timedelta(days=1)
        self.stock.quantity = 5
        self.stock.save()
        self.assertEqual(InventoryStock.objects.get(id=self.stock.id).quantity, 5)


class StockRecordTestCase(TestCase):
    def setUp(self):
        """Set up an inventory item and user for transactions"""
        self.item = create_test_item()
        self.stock = create_test_stock(self.item)
        self.user = User.objects.create_user(
            email="test_email@example.com",
            password="1234"
        )

    def test_deletion_of_record_restores_stock(self):
        transaction = InventoryTransaction.objects.create(
            item=self.item,
            created_by=self.user,
            quantity=1,
        )
        for i in StockRecord.objects.filter(transaction=transaction):
            i.delete()
        self.assertFalse(
            StockRecord.objects.filter(transaction=transaction).exists()
        )
        self.assertEqual(
            self.stock.quantity,
            5
        )
    def test_deletion_of_records_restores_stock(self):
        create_test_stock(self.item)
        self.assertEqual(
            InventoryStock.objects.filter(item=self.item).aggregate(Sum('quantity'))["quantity__sum"],
            10
        )
        transaction = InventoryTransaction.objects.create(
            item=self.item,
            created_by=self.user,
            quantity=6,
        )
        for i in StockRecord.objects.filter(transaction=transaction):
            i.delete()
        self.assertFalse(
            StockRecord.objects.filter(transaction=transaction).exists()
        )
        self.assertEqual(
            InventoryStock.objects.filter(item=self.item).aggregate(Sum('quantity'))["quantity__sum"],
            10
        )
