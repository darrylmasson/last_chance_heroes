import lch
#from lch import Weapon, Model, Team, NoRangedWeapon

__all__ = 'TestTeam1 TestTeam2'.split()

TestRifle1 = lch.RangedWeapon(name='Test R1', range=18, attacks=1, punch=0, min_damage=2, max_damage=4)
TestHeavy1 = lch.RangedWeapon(name='Test RH', range=24, attacks=3, punch=1, min_damage=3, max_damage=5, category="heavy")
TestRifle2 = lch.RangedWeapon(name='Test R2', range=12, attacks=2, punch=0, min_damage=3, max_damage=4)
TestAssault2 = lch.RangedWeapon(name='Test RA', range=12, attacks=3, punch=1, min_damage=3, max_damage=4, category="assault")
NoRangedWeapon = lch.RangedWeapon(name="None", range=-1, attacks=0)

Knife = lch.MeleeWeapon(name='Knife', min_damage=2, max_damage=3)
Sword = lch.MeleeWeapon(name='Sword', attacks=2, min_damage=3, max_damage=4)
Axe = lch.MeleeWeapon(name='Axe', attacks=3, min_damage=3, max_damage=5)

test_1_kwargs={'movement': 6, 'ranged_skill': 55, 'ranged_consistency': 15,'armor':2,
        'melee_skill': 45, 'melee_consistency': 15, 'dodge': 60, 'health': 6}
TestModel1 = lch.Model(name='Test1', melee_weapon=Knife, ranged_weapon=TestRifle1, **test_1_kwargs)
TestModel1a = lch.Model(name='Test1a', melee_weapon=Knife, ranged_weapon=TestHeavy1, **test_1_kwargs)
TestModel1b = lch.Model(name='Test1b', melee_weapon=Sword, ranged_weapon=NoRangedWeapon, **test_1_kwargs)

test_2_kwargs={'movement': 6, 'ranged_skill': 45, 'ranged_consistency': 25,'armor': 1,
        'melee_skill': 60, 'melee_consistency': 20, 'dodge': 50, 'health': 7}
TestModel2 = lch.Model(name='Test1', melee_weapon=Sword, ranged_weapon=TestRifle2, **test_2_kwargs)
TestModel2a = lch.Model(name="Test2a", melee_weapon=Sword, ranged_weapon=TestAssault2, **test_2_kwargs)
TestModel2b = lch.Model(name='Test2b', melee_weapon=Axe, ranged_weapon=NoRangedWeapon, **test_2_kwargs)

def TestTeam1():
    return lch.Team([TestModel1, TestModel1a, TestModel1b])

def TestTeam2():
    return lch.Team([TestModel2, TestModel2a, TestModel2b])
