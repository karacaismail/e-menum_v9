"""
Tests for apps.seo_shield.models.

Covers BotWhitelist, IPRiskScore, RuleSet (with soft delete), and BlockLog
model creation, defaults, constraints, string representations, and ordering.
"""

import uuid

from django.db import IntegrityError
from django.test import TestCase

from apps.seo_shield.models import BlockLog, BotWhitelist, IPRiskScore, RuleSet


class BotWhitelistModelTests(TestCase):
    """Tests for the BotWhitelist model."""

    def test_create_basic(self):
        """BotWhitelist can be created with required fields."""
        bot = BotWhitelist.objects.create(
            name='Googlebot',
            user_agent_pattern=r'Googlebot',
        )
        self.assertIsInstance(bot.id, uuid.UUID)
        self.assertEqual(bot.name, 'Googlebot')
        self.assertTrue(bot.is_active)

    def test_default_verification_method(self):
        """Default verification_method should be 'dns'."""
        bot = BotWhitelist.objects.create(
            name='TestBot',
            user_agent_pattern=r'TestBot',
        )
        self.assertEqual(bot.verification_method, BotWhitelist.VerificationMethod.DNS)

    def test_verification_method_choices(self):
        """All VerificationMethod choices are accepted."""
        for method in BotWhitelist.VerificationMethod:
            bot = BotWhitelist.objects.create(
                name=f'Bot_{method.value}',
                user_agent_pattern=f'Bot_{method.value}',
                verification_method=method,
            )
            self.assertEqual(bot.verification_method, method)

    def test_ip_ranges_default_is_list(self):
        """ip_ranges defaults to an empty list."""
        bot = BotWhitelist.objects.create(
            name='Bot',
            user_agent_pattern=r'Bot',
        )
        self.assertEqual(bot.ip_ranges, [])

    def test_last_verified_null_by_default(self):
        """last_verified is null by default."""
        bot = BotWhitelist.objects.create(
            name='Bot',
            user_agent_pattern=r'Bot',
        )
        self.assertIsNone(bot.last_verified)

    def test_str_representation(self):
        """__str__ returns the bot name."""
        bot = BotWhitelist(name='Googlebot', user_agent_pattern=r'Googlebot')
        self.assertEqual(str(bot), 'Googlebot')

    def test_ordering_by_name(self):
        """BotWhitelist records are ordered by name."""
        BotWhitelist.objects.create(name='Zbot', user_agent_pattern=r'Zbot')
        BotWhitelist.objects.create(name='Abot', user_agent_pattern=r'Abot')
        bots = list(BotWhitelist.objects.values_list('name', flat=True))
        self.assertEqual(bots, ['Abot', 'Zbot'])


class IPRiskScoreModelTests(TestCase):
    """Tests for the IPRiskScore model."""

    def test_create_basic(self):
        """IPRiskScore can be created with just an ip_address."""
        ip = IPRiskScore.objects.create(ip_address='192.168.1.1')
        self.assertIsInstance(ip.id, uuid.UUID)
        self.assertEqual(ip.risk_score, 0)
        self.assertEqual(ip.total_requests, 0)
        self.assertFalse(ip.is_whitelisted)
        self.assertFalse(ip.is_blacklisted)

    def test_unique_ip_address(self):
        """ip_address must be unique."""
        IPRiskScore.objects.create(ip_address='10.0.0.1')
        with self.assertRaises(IntegrityError):
            IPRiskScore.objects.create(ip_address='10.0.0.1')

    def test_risk_score_stored(self):
        """risk_score value is correctly stored."""
        ip = IPRiskScore.objects.create(ip_address='10.0.0.2', risk_score=75)
        ip.refresh_from_db()
        self.assertEqual(ip.risk_score, 75)

    def test_signals_default_is_dict(self):
        """signals defaults to an empty dict."""
        ip = IPRiskScore.objects.create(ip_address='10.0.0.3')
        self.assertEqual(ip.signals, {})

    def test_str_representation(self):
        """__str__ shows IP and score."""
        ip = IPRiskScore(ip_address='1.2.3.4', risk_score=42)
        self.assertEqual(str(ip), '1.2.3.4 (score=42)')

    def test_timestamps_auto_set(self):
        """first_seen and last_seen are automatically set."""
        ip = IPRiskScore.objects.create(ip_address='10.0.0.4')
        self.assertIsNotNone(ip.first_seen)
        self.assertIsNotNone(ip.last_seen)


class RuleSetModelTests(TestCase):
    """Tests for the RuleSet model, including soft delete behavior."""

    def test_create_basic(self):
        """RuleSet can be created with required fields."""
        rs = RuleSet.objects.create(name='Block scanners')
        self.assertIsInstance(rs.id, uuid.UUID)
        self.assertTrue(rs.is_active)
        self.assertEqual(rs.action, RuleSet.Action.LOG)
        self.assertEqual(rs.priority, 100)

    def test_soft_delete(self):
        """soft_delete sets deleted_at and hides from default manager."""
        rs = RuleSet.objects.create(name='Temp rule')
        rs.soft_delete()
        self.assertTrue(rs.is_deleted)
        self.assertEqual(RuleSet.objects.filter(pk=rs.pk).count(), 0)
        self.assertEqual(RuleSet.all_objects.filter(pk=rs.pk).count(), 1)

    def test_restore_after_soft_delete(self):
        """restore clears deleted_at and makes record visible again."""
        rs = RuleSet.objects.create(name='Restorable rule')
        rs.soft_delete()
        rs.restore()
        self.assertFalse(rs.is_deleted)
        self.assertEqual(RuleSet.objects.filter(pk=rs.pk).count(), 1)

    def test_ordering_by_priority(self):
        """RuleSets are ordered by priority (ascending)."""
        RuleSet.objects.create(name='Low priority', priority=200)
        RuleSet.objects.create(name='High priority', priority=10)
        names = list(RuleSet.objects.values_list('name', flat=True))
        self.assertEqual(names, ['High priority', 'Low priority'])

    def test_rules_default_is_list(self):
        """rules field defaults to an empty list."""
        rs = RuleSet.objects.create(name='Default rules')
        self.assertEqual(rs.rules, [])

    def test_str_representation(self):
        """__str__ returns the rule set name."""
        rs = RuleSet(name='My Rule')
        self.assertEqual(str(rs), 'My Rule')

    def test_action_choices(self):
        """All Action choices are accepted."""
        for action in RuleSet.Action:
            rs = RuleSet.objects.create(name=f'Rule_{action.value}', action=action)
            self.assertEqual(rs.action, action)


class BlockLogModelTests(TestCase):
    """Tests for the BlockLog model."""

    def test_create_basic(self):
        """BlockLog can be created with required fields."""
        log = BlockLog.objects.create(
            ip_address='192.168.1.100',
            path='/wp-admin',
            method='GET',
            reason='risk_threshold',
        )
        self.assertIsInstance(log.id, uuid.UUID)
        self.assertEqual(log.action_taken, BlockLog.ActionTaken.LOGGED)
        self.assertEqual(log.response_code, 200)

    def test_fk_to_ruleset(self):
        """BlockLog can reference a RuleSet via FK."""
        rs = RuleSet.objects.create(name='Scanner block')
        log = BlockLog.objects.create(
            ip_address='10.0.0.5',
            path='/test',
            method='GET',
            reason='rule_match',
            rule=rs,
        )
        self.assertEqual(log.rule, rs)
        self.assertIn(log, rs.block_logs.all())

    def test_fk_ruleset_set_null_on_delete(self):
        """Deleting a RuleSet sets BlockLog.rule to NULL."""
        rs = RuleSet.all_objects.create(name='Deletable rule')
        log = BlockLog.objects.create(
            ip_address='10.0.0.6',
            path='/test',
            method='GET',
            reason='rule_match',
            rule=rs,
        )
        rs.delete()  # Physical delete for this test
        log.refresh_from_db()
        self.assertIsNone(log.rule)

    def test_str_representation(self):
        """__str__ shows action, IP, method, and path."""
        log = BlockLog(
            ip_address='1.2.3.4',
            path='/evil',
            method='POST',
            reason='test',
            action_taken=BlockLog.ActionTaken.BLOCKED,
        )
        self.assertEqual(str(log), '[blocked] 1.2.3.4 POST /evil')

    def test_signals_default_is_dict(self):
        """signals defaults to an empty dict."""
        log = BlockLog.objects.create(
            ip_address='10.0.0.7',
            path='/',
            method='GET',
            reason='test',
        )
        self.assertEqual(log.signals, {})

    def test_ordering_by_created_at_desc(self):
        """BlockLogs are ordered by created_at descending."""
        log1 = BlockLog.objects.create(
            ip_address='10.0.0.8', path='/', method='GET', reason='a',
        )
        log2 = BlockLog.objects.create(
            ip_address='10.0.0.9', path='/', method='GET', reason='b',
        )
        logs = list(BlockLog.objects.all())
        self.assertEqual(logs[0].pk, log2.pk)
        self.assertEqual(logs[1].pk, log1.pk)
