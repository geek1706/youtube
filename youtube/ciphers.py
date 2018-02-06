import json
import re
from pathlib import Path
from urllib import request

DIR = Path(__file__, '../data')
CIPHERS = DIR / 'ciphers.json'


def update(player):
    """Find and update the cipher.

    Args:
        player (dict): Contains the 'sts' value and URL of the YouTube player.

    Returns:
        str: The cipher that corresponding to the 'sts' value.

    """
    sts = player['sts']
    url = player['url']
    cipher = []

    with request.urlopen(url) as file:
        player = file.read().decode('utf-8')

    name = re.search(r'"signature",(\w*)\(', player).group(1)

    body = '{0}=function\(a\){{(a=a\.split.*?)}};'.format(name)
    body = re.search(body, player).group(1).split(';')[1:-1]

    var = re.search(r'(\w*)\.', body[0]).group(1)

    functions = 'var {0}={{(.*?)}};'.format(var)
    functions = re.search(functions, player, re.DOTALL).group(1)

    # Example:
    # name = 'DK'
    # body = ['CK.ng(a,3)', 'CK.AE(a,7)', 'CK.XN(a,49)']
    # var = 'CK'
    # functions = 'XN:function(a,b){var c=a[0];a[0]=a[b%a.length];a[b]=c}',
    # 'AE:function(a){a.reverse()}, ng:function(a,b){a.splice(0,b)}'
    #
    # What does this mean?
    # 'CK.ng(a,3)' – slice the signature from character [3] to the end;
    # 'CK.AE(a,7)' – reverse;
    # 'CK.XN(a,49)' – swap [0] and [49] character.
    #
    # Decipher:
    # s = 76D76D93CC670CDC94B23703E52E298ECA620E69BE4.03CD2DF6066391A54D7D96089F98CCB51D8912A6
    #
    # Slice:
    # s = s[3:]
    # 76D93CC670CDC94B23703E52E298ECA620E69BE4.03CD2DF6066391A54D7D96089F98CCB51D8912A6
    #
    # Reverse:
    # s = s[::-1]
    # 6A2198D15BCC89F98069D7D45A1936606FD2DC30.4EB96E026ACE892E25E30732B49CDC076CC39D67
    #
    # Swap:
    # s[0], s[49] = s[49], s[0]
    # 6A2198D15BCC89F98069D7D45A1936606FD2DC30.4EB96E026ACE892E25E30732B49CDC076CC39D67
    #
    # We got the valid signature ;)

    for operation in body:
        name = re.search(r'\w+\.(\w+)', operation).group(1)
        value = re.search(r'\(\w*,(\d*)\)', operation).group(1)

        if re.search(name + r':function.*(splice).*', functions):
            cipher.append('s{0}'.format(value))  # s – the slice method.

        elif re.search(name + r':function\(\w+\)', functions):
            cipher.append('r{0}'.format(value))  # r – the reverse method.

        elif re.search(name + r':function.*(length).*', functions):
            cipher.append('w{0}'.format(value))  # w – the swap method.

    cipher = ' '.join(cipher)

    # Add the new cipher to the ../data/ciphers.json file.
    if DIR.exists() and CIPHERS.exists():
        try:
            with CIPHERS.open('r+') as file:
                ciphers = json.load(file)
                ciphers.update({sts: cipher})
                file.seek(0)
                json.dump(ciphers, file, indent=2)
                file.truncate()
        except json.decoder.JSONDecodeError:
            pass
    else:
        # Create the new directory and ../data/ciphers.json file.
        DIR.mkdir(parents=True, exist_ok=True)
        CIPHERS.touch()
        with CIPHERS.open('w') as file:
            json.dump({sts: cipher}, file, indent=2)

    return cipher


def get(player):
    """Get the cipher that corresponding to the YouTube player version.

    Args:
        player (dict): Contains the 'sts' value and URL of the YouTube player.

    Note:
       If the cipher is missing in known ciphers, then the 'update' method will be used.

    """
    if DIR.exists() and CIPHERS.exists():
        try:
            if CIPHERS.stat().st_size > 0:
                with CIPHERS.open('r') as file:
                    ciphers = json.load(file)
                    cipher = ciphers.get(player['sts'])
                    return cipher
        except json.decoder.JSONDecodeError:
            pass
    else:
        cipher = update(player)
        return cipher


def decipher(signature, cipher):
    """Decipher the signature."""
    signature = list(signature)
    cipher = cipher.split(' ')

    for operation in cipher:
        n = int(operation[1:])
        if operation[0] is 's':
            signature = signature[n:]
        elif operation[0] is 'r':
            signature = signature[::-1]
        elif operation[0] is 'w':
            signature[0], signature[n] = signature[n], signature[0]

    return ''.join(signature)
