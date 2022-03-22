#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# KlipChop menu function


# All kllipchop customizable modules must have a main function
# The main function is passed three variables:
#   textlines   - Generator of clipboard lines
#   messagefunc - function to call with notification
#   config      - configuration dictionary
# The main function should return a string object or a list of strings


import re
from dataclasses import dataclass

from OuiLookup import OuiLookup

RAIDMODEL = {
    '00': 'DF',
    '01': '7700E',
	'02': '9900/RAID400',
	'03': '9900V/RAID450',
	'04': 'USP/RAID500',
	'14': 'NSC55/RAID500',
	'05': 'USPV/RAID600"',
	'15': 'USPV/RAID600',
	'06': 'VSP',
	'16': 'VSP',
	'13': 'HUSVM',
	'12': 'VSP G/Fxx0/E990',
	'22': 'VSP G/Fxx0/E990',
	'07': 'VSP G1000',
	'17': 'VSP G1000',
	'10': 'DF',
	'08': 'VSP 5000',
	'18': 'VSP 5000',
    '21': 'VSP Ex90',
    '31': 'VSP Ex90',
}

RAIDSNHEXPREFIX = {
    '14': '1',
    '15': '1',
    '16': '1',
    '22': '1',
    '17': '1',
    '18': '1',
    '31': '1',
}

RAIDSNPREFIX = {
    '13': '2',
    '12': '4',
    '22': '4',
    '21': '6',
    '31': '6',
}

RAIDPORTLETS =  { k:v for k,v in enumerate('ABCDEFGHJKLMNPQR') }
RAIDCLUSTERLETS = { k:v for k,v in enumerate('123456789ABCDEFG') }


#   < DF Range of serial number >
#          DF800H/EH      DF800M/EM      DF800S/ES/EXS  SA800          SA810          DF850MH/S/XS
#   RSD    010001-020000  010001-020000  010001-020000  010001-130000  010001-130000  010001-050000
#   HICAM  040001-046000  040001-046000  040001-046000  n/a            n/a            Same as above
#   HICEF  050001-056000  050001-056000  050001-056000  n/a            n/a            Same as above

#
# 8-digit  serial numbers are 
# 8701xxxx   DF800h  , ams 2500
# 8501xxxx   DF800m , ams 2300
# 8301xxxx   DF800s  ,ams  2100
# 8201xxxx   SA810    , sms  810  (same as below just more drives )
# 8101xxxx   SA800    , sms  800
#
#   DF800M = Port 0A - 50060e8010253050				
#            Port 1A - 50060e8010253054				
#   DF800H = Port 0A - 50060e801004e580				
#            Port 1A - 50060e801004e588				
#   DF850MH= Port 0A - 50060e801009C410				
#            Port 1A - 50060e801009C418				
#                      IHHHHHHT0MSssssP				
#   IHHHHHH = Vender ID(fixed value)  = 50060e8
#   TOM = Product code(fixed value, DF700/DF800/SA/DF850) = 010
#   S = Type
#       DF800H/EH       ：0
#       DF850MH         ：1
#       DF800M/EM       ：2
#       DF850S          ：3
#       DF800S/ES/EXS   ：4
#       DF850XS         ：5
#       SA800           ：8 or 9(If serial number is more than 65536(Dec), S is 9)
#       SA810           ：A or B(If serial number is more than 65536(Dec), S is B) <- Not GAed
#   ssss = Serial number
#          In case of "RSD" AND "DF800S/M/H/EXS/ES/EM/EH":
#             Result of Serial#(6 digit)+10000(decimal) is converted to hexadecimal(4 hex string)
#          In case of ("HICAM" OR "HICEF") AND "DF800S/M/H/EXS/ES/EM/EH":
#             Result of Serial#(6 digit)+3000(decimal) is converted to hexadecimal(4 hex string)
#          In case of SA800/SA810:
#             Low 4 digit of Serial# is converted to hexadecimal(4 hex string)
#             If the high-order digit is 1 (=serial number is more than 65536(Dec)),
#             Result of 1+S(Type) is set to S(Type).
#          In case of DF850:
#             Result of Serial#(6 digit)+70000(decimal) is converted to hexadecimal(4 hex string)
#             The high-order digit is ignored if the result is larger than 4 hex string.
#   P = Port number
#       SA800/SA810       ：0～3
#       DF800S/ES/EXS     ：0～3
#       DF800M/EM         ：0～7
#       DF800H/EH         ：0～F
#       DF850MH/S/XS      ：0～F


DFMODEL = {
    '00000': 'DF500/9200',
    '10004': 'DF600/9570V',
    '1000C': 'DF600/9580V',

    '10100': 'DF700H/AMS1000',
    '10102': 'DF700M/AMS500',
    '10104': 'DF700S/AMS200',
    '00106': 'DF700XS/WMS100',

    '20100': 'DF800H/AMS2500',
    '20102': 'DF800M/AMS2300',
    '20104': 'DF800S/AMS2100',

    '10101': 'DF850MH/HUS150',
    '10103': 'DF850S/HUS130',
    '10105': 'DF850XS/HUS110',
}

DFSNPREFIX = {
    '00000': '',
	'10004': '6501',
	'1000C': '6801',

	'10100': '7701',
	'10102': '7501',
	'10104': '7301',
	'00106': '7100',

	'20100': '8701',
	'20102': '8501',
	'20104': '8301',

    '10101': '930',
    '10103': '92x',
    '10105': '91x'
}

DFPORTCOUNT = {
    '00000': 1,
	'10004': 2,
	'1000C': 4,

	'10100': 4,
	'10102': 2,
	'10104': 1,
	'00106': 1,

	'20100': 8,
	'20102': 4,
	'20104': 2,

    '10101': 8,
    '10103': 8,
    '10105': 8,
}

DFPORTS = { # Count of ports to letters for each CTL0+1:
    1: { k:v for k,v in enumerate('AA') },
	2: { k:v for k,v in enumerate('ABAB') },
	4: { k:v for k,v in enumerate('ABCDABCD') },
	8: { k:v for k,v in enumerate('ABCDEFGHABCDEFGH') },
}


# Hitachi storage pattern for address type 5 (WWN):
# (note the negative lookback and forward assertions to ensure it's not in a long string digits)
RAIDWWN = re.compile(r'(?<![\dA-Z])5([\dA-F]{6})([\dA-F])([\dA-F]{2})([\dA-F]{4})([\dA-F])([\dA-F])(?![\dA-Z])', re.IGNORECASE)
    # 1 = OUI, Hitachi = 0060E8
    # 2 = ? usually 0
    # 3 = MajorModel
    # 4 = Serial Hex (partial in some models)
    # 5 = Cluster
    # 6 = Port

# Hitachi storage pattern for address type 6 (NAA):
# (note the negative lookback and forward assertions to ensure it's not in a long string digits)
RAIDNAA = re.compile(r'(?<![\dA-Z])6([\dA-F]{6})([\dA-F]{3})([\dA-F])....([\dA-F]{4}})([\dA-F]{5})....([\dA-F]{4})(?![\dA-Z])', re.IGNORECASE)
    # 1 = OUI, Hitachi = 0060E8
    # 2 = RAID Model (we use the right 2 digits only)
    # 3 = Midrange Type
    # ??? next 4 chars skipped
    # 4 = MR serial prefix
    # 5 = Serial
    # ??? next 4 chars skipped
    # 6 = LDEV

# oui, dftype, snx, port:
DFWWN = re.compile(r'(?<![\dA-Z])5([\dA-F]{6})([\dA-F]{4})([\dA-F]{4})([\dA-F])(?![\dA-Z])', re.IGNORECASE)


# General pattern for IEEE addresses of type 1/2/5/6:
# (note the negative lookback and forward assertions to ensure it's not in a long string digits)
ADDRESSPAT = re.compile(r'(?<![\dA-Z])[1256][\dA-F]{15}(?![\dA-Z])', re.IGNORECASE)


def ouidecoder(text):
    """ Find OUI from 16 byte addresses in text """

    text = re.sub(r'[-:]', '', text)
    if not(text.strip()): return None

    result = list()
    ieeelookup = list()
    for address in ADDRESSPAT.findall(text):
        m = RAIDWWN.search(address)
        if m:
            oui, _, model, snx, clusterx, portx = m.groups()
        else:
            m = RAIDNAA.search(address)
            if m:
                oui, model, snx, mrtype, mrsnp, snx, ldev = m.groups()
        if not m: continue  # Not a recognised address
        if oui.upper() != '0060E8':   # Not Hitachi storage
            ieeelookup.append(oui)
            continue

        if address.startswith('5'):   # We have a storage system
            modelname = RAIDMODEL.get(model, None)
            if modelname and modelname != 'DF':
                serialnox = RAIDSNHEXPREFIX.get(model, '') + snx
                serialno = RAIDSNPREFIX.get(model, '') + str(int(serialnox, 16))
                portn = int(portx, 16)
                clustern = int(clusterx, 16)
                port = RAIDCLUSTERLETS.get(clustern, '?') + RAIDPORTLETS.get(portn, '?')
                result.append(f'Hitachi {modelname} SN:{serialno} Port:{port}')
            elif modelname == 'DF':
                result.append(f'Hitachi Unsupported DF system')
                # m = DFWWN.search(address)
                # if m:
                #     oui, dftype, dfsnx, dfportx = m.groups()
                # dfserialno = int(dfsnx, 16)
                # dfmodel = int(f'{dfserialno:05d}'[0] + dftype)
                # if DFMODEL.get(str(dfmodel), '').startswith('DF850'):
                #     dfserialno = int('1' + dfsnx, 16) -70000
                # else:
                #     if 20001 <= dfserialno <= 30000:  # DF800 RSD manufactured
                #         dfserialno -= 10000 
                #     if 43001 <= dfserialno <= 49000:  # DF800 HICAM manufactured
                #         dfserialno -= 3000
                #         dfmodel -= 20000
                #     if 50001 <= dfserialno <= 56000:  # DF800 HICEF manufactured
                #         dfmodel -= 30000

                # dfmodel = str(dfmodel)
                # dfserialno = DFSNPREFIX.get(dfmodel, '') + f'{dfserialno:05d}'
                # dfmodelname = DFMODEL.get(dfmodel, None)
                # if dfmodelname:
                #     dfportn = int(dfportx, 16)
                #     dfpc = DFPORTCOUNT.get(dfmodel, None)
                #     if dfpc:
                #         dfctl = '1' if dfportn >= dfpc else '0'
                #         dfport = DFPORTS[dfpc][dfportn]
                #     else:
                #         dfctl = '?'
                #         dfport = '?'
                #     result.append(f'Hitachi {dfmodelname} SN:{dfserialno} Port:{dfctl}{dfport}')
                # else:
                #     ieeelookup.append(oui)
            else:
                ieeelookup.append(oui)

    
    # Find other Vendors
    if ieeelookup:
        ld = OuiLookup().query(' '.join(ieeelookup))   # returns a list of dicts: [{oui:vendor},...,...]
        result.extend([v for x in ld for v in x.values()])

    return result


def main(textlines, messagefunc, config):
    """
    KlipChop func to annotate WWN with decodes of Hitachi Storage
    """

    tag = '   #'
    result = []
    count = 0
    for line in textlines():
        decodes = ouidecoder(line)
        if decodes:
            line = line + tag + tag.join(decodes)
            count += len(decodes)

        if config['extract-WWN'] and not decodes:
            continue
        result.append(line)
        
    result = '\n'.join(result)
    messagefunc(f'Annotated {count} OUI')
    return result


if __name__ == '__main__':

    testtxt = '''
E790    641096  port 3A     50060e8021a08820
E990    448576  port 1A     50060e8012bdc000
R900    33484   port 7C     50060E800882CC62
G900    446149  port 8B     50060e8012b44571
Gx00    485038              50060e80224c2e21
Gx00	410116	4D          50060E8012278433
G1000	56456	BA          50:06:0e:80:07:dc:88:a0
G800    412575  port 8D     50060e8012311f73
VSP	    65779	1A          50060e801600f300
HUS VM	210035              50060e8013273370
9900	10045	1E          50060E8002273D04
9900V	20055	2A          50060e80034e5710
AMS500	75011253	0A      50060e8010253050
AMS2500	87010083	1H      50060E801004E73F
HUS 150	93010013	1H      50060E80101388DF
HUS 110 91x40029    0A      50060E80105ADCD0
HUS 130 92x10159    0A      50060E80103391F0
'''

    for line in testtxt.splitlines():
        line = line.strip()
        if line:
            print(f'{line}\t{ouidecoder(line)}')


    