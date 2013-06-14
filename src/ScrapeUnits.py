'''
Created on 13 jun 2013

@author: eluksan
'''

from bs4 import BeautifulSoup
import re

class Unit(object):
    def __init__(self, soup_tag):
        self.t = soup_tag
        t = soup_tag
        name = t.find('p').text.strip()
        m = re.match('(.*) \((\w+)\)$', name) # filter out Name (abbrev)
        (self.name, self.abbrev) = m.groups()

        self.phase = 2
        self.splash_damage = False
        self.weakest_target = False
        self.tower_bonus = False

        attrs = t.find(name = 'ul', class_ = 'unit_attributes')
        attr_re = re.compile('(\w+(?:\. \w+)?).*?(\d+)', re.DOTALL + re.MULTILINE)
        for attr in attrs.find_all('li'):
            a = attr.text
            if "Last Strike" in a: self.phase = 3; continue
            if "First Strike" in a: self.phase = 1; continue
            if "Splash" in a: self.splash_damage = True; continue
            if "weakest" in a: self.weakest_target = True; continue
            if "Tower" in a: self.tower_bonus = True; continue
            m = attr_re.search(a)
            if not m:
                #print a
                continue
            (x,y) = m.groups()
            if "HP" == x: self.hp = int(y)
            if "Min. damage" == x: self.dmg_min = int(y)
            if "Max. damage" == x: self.dmg_max = int(y)
            if "Accuracy" == x: self.accuracy = int(y)*0.01
            if "Experience" == x: self.experience = int(y)
    
    def __eq__(self, unit):
        return self.abbrev == unit.abbrev

    def __str1__(self):
        return self.abbrev

    def __str2__(self):
        x = self.name + " [" + self.abbrev + "]"
        x += "\nHP: %i" % (self.hp)
        x += "\nDamage: %i / %i" % (self.dmg_min, self.dmg_max)
        x += "\nAccuracy: %i%%" % (int(self.accuracy*100),)
        x += "\nExp: %i" % (self.experience)
        if self.phase == 1: x += "\nFirst Strike"
        if self.phase == 3: x += "\nLast Strike"
        if self.tower_bonus: x += "\nTower bonus"
        if self.splash_damage: x += "\nSplash damage"
        if self.weakest_target: x += "\nWeakest target"
        return x
    
    def __str__(self):
        x = self.name + ", " + self.abbrev
        x += ", %i" % (self.hp)
        x += ", %i, %i" % (self.dmg_min, self.dmg_max)
        x += ", %i%%" % (int(self.accuracy*100),)
        x += ", %i" % (self.experience)
        x += ", %i" % (self.phase)
        if self.tower_bonus: x += ", Yes"
        else: x += ", No"
        if self.splash_damage: x += ", Yes"
        else: x += ", No"
        if self.weakest_target: x += ", Yes"
        else: x += ", No"
        return x


class AdventureTab(object):
    '''
    classdocs
    '''
    def __init__(self, tab_id, filehandle):
        self.tab_id = tab_id
        self.soup = BeautifulSoup(filehandle)
        self.units = []
        units = self.soup.find_all(name = 'div', class_='tooltip')
        for u in units:
            self.units.append(Unit(u))

def get_adventure_ids(url_opener):
    html = url_opener.open('http://settlersonlinesimulator.com/dso_kampfsimulator/en/')
    soup = BeautifulSoup(html)
    r = re.compile('id=(\d+)')
    sel = soup.find("select", attrs={"name": "adventure"})
    advs = []
    for adv_t in sel.find_all("option"):
        m = r.search(adv_t['value'])
        if not m:
            continue
        advs.append(m.group(1))
    return advs

def get_adv(opener, adv_id, load_web = False):
    filename = 'adv_tab_%s.html'%(adv_id) 
    if load_web:
        html = opener.open('http://settlersonlinesimulator.com/dso_kampfsimulator/includes/adventure.tab.php?adventure_id=%s'%(adv_id))
        t = open(filename, 'w')
        t.write(html.read())
        t.close()
        html.close()
    try:
        html = open(filename)
    except:
        if load_web: raise
        return get_adv(opener, adv_id, True)
    return AdventureTab(adv_id, html)

def merge_adventure_tabs(tab_list):
    l = [x.units for x in tab_list]
    return merge_unit_lists(l)

def merge_unit_lists(lists, Acc = []):
    lists = [x for x in lists if x] # remove empty lists
    if not lists:
        return Acc
    for list_idx1 in range(len(lists)):
        found = [list_idx1]
        for list_idx2 in range(len(lists)):
            if lists[list_idx1][0] == lists[list_idx2][0]:
                found.append(list_idx2)
            elif lists[list_idx1][0] in lists[list_idx2]:
                break
        else:
            Acc.append(lists[list_idx1][0])
            for f in found:
                lists.insert(0, lists.pop(f)[1:])
            return merge_unit_lists(lists, Acc)
    print "fail"
    print lists
    print Acc
    
def save_merged_units(ulist):
    f = open('enemy_units.csv', 'w')
    f.write("Defend order, Name, Abbrev, HP, Dmg min, Dmg max, Accuracy, Exp., Attack phase, Tower bonus, Splash dmg, Weakest target\n")
    for n in range(len(ulist)):
        f.write(str(n+1)+ ", ")
        f.write(str(ulist[n]))
        f.write("\n")
    f.close()

if __name__ == '__main__':
    import urllib2
    opener = urllib2.build_opener()
    opener.addheaders.append(('Cookie', 'PHPSESSID=5d79b7dc798506423890e30cf41a4fa3')) # Use a session with English translation
    
    advs = get_adventure_ids(opener)
    A = [ get_adv(opener, adv_id) for adv_id in advs ]
    merged = merge_adventure_tabs(A)
    save_merged_units(merged)
    #print [x.abbrev for x in merged]