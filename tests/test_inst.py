import lch
#from lch import Weapon, Model, Team, NoRangedWeapon

__all__ = 'TestTeam1 TestTeam2'.split()

TestRifle1 = lch.RangedWeapon(name='Test R1', range=18, attacks=1, punch=0, min_damage=2, max_damage=4)
TestHeavy1 = lch.RangedWeapon(name='Test RH', range=24, attacks=3, punch=1, min_damage=3, max_damage=5, category="heavy")
TestRifle2 = lch.RangedWeapon(name='Test R2', range=12, attacks=2, punch=0, min_damage=3, max_damage=4)
TestAssault2 = lch.RangedWeapon(name='Test RA', range=12, attacks=3, punch=1, min_damage=3, max_damage=4, category="assault")
NoRangedWeapon = lch.RangedWeapon(name="None", range=-1, attacks=0)
#print(NoRangedWeapon.hash)

Knife = lch.MeleeWeapon(name='Knife', min_damage=2, max_damage=3)
Sword = lch.MeleeWeapon(name='Sword', attacks=2, min_damage=3, max_damage=4)
Axe = lch.MeleeWeapon(name='Axe', attacks=3, min_damage=3, max_damage=5)

test_1_kwargs={'move': 6, 'rs': 55, 'rc': 15,'armor':2,
        'ms': 45, 'mc': 15, 'dodge': 60, 'max_health': 6}
TestModel1 = lch.Model(mw=Knife, rw=TestRifle1, **test_1_kwargs)
TestModel1a = lch.Model(mw=Knife, rw=TestHeavy1, **test_1_kwargs)
TestModel1b = lch.Model(mw=Sword, rw=NoRangedWeapon, **test_1_kwargs)

test_2_kwargs={'move': 6, 'rs': 45, 'rc': 25,'armor': 1,
        'ms': 60, 'mc': 20, 'dodge': 50, 'max_health': 7}
TestModel2 = lch.Model(mw=Sword, rw=TestRifle2, **test_2_kwargs)
TestModel2a = lch.Model(mw=Sword, rw=TestAssault2, **test_2_kwargs)
TestModel2b = lch.Model(mw=Axe, rw=NoRangedWeapon, **test_2_kwargs)

def TestTeam1(ai):
    return lch.Team([TestModel1, TestModel1a, TestModel1b], ai)

def TestTeam2(ai):
    return lch.Team([TestModel2, TestModel2a, TestModel2b], ai)
