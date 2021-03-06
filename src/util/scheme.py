import sys,logging
from charm.toolbox.pairinggroup import PairingGroup, GT
from charm.toolbox.symcrypto import SymmetricCryptoAbstraction
from charm.core.math.pairing import hashPair as extractor
from charm.schemes.abenc.abenc_yang15 import CPabe_yang15


class Scheme:
    def __init__(self, group=PairingGroup("SS512")):
        self.group = group
        self.cpabe = CPabe_yang15(group)
        self.users = dict()
        self.delegation = dict()

    def setup(self):
        (cloud_pk, cloud_msk) = self.cpabe.setup()
        return cloud_pk, cloud_msk

    # CAUTIOUS: NEED TO REMOVE THIS FUNCTION IN THE END. KEYGEN_USER
    #     IS NOT SUPPOSED TO BE IMPLMENTED HERE
    def keygen_user(self, cloud_pk, user):
        pk_u, sk_u = self.cpabe.keygen_user(cloud_pk)
        self.users[pk_u] = user
        return pk_u, sk_u

    def keygen_proxy(self, cloud_pk, cloud_msk, pk_u, pk_cs, attrs):
        try:
            pxy_k_u = self.cpabe.keygen_proxy(cloud_pk, cloud_msk, pk_u, pk_cs, attrs)
            user = self.users[pk_u]
            try:
                self.delegation[user].append(pxy_k_u)
            except KeyError:
                self.delegation[user] = [pxy_k_u]
            return pxy_k_u
        except Exception as e:
            print("Unexpected error:", str(e))

    def random_pair(self):
        return self.group.random(GT)

    def encrypt_text(self, pt, secret):
        try:
            k = extractor(secret)
            symcrypt = SymmetricCryptoAbstraction(k)
            ct = symcrypt.encrypt(pt)
            return ct
        except Exception as e:
            print("Unexpected error:", str(e))

    def encrypt_secret(self, aes_key_pt, cloud_pk, access_policy):
        try:
            aes_key_ct = self.cpabe.encrypt(cloud_pk, aes_key_pt, access_policy)
            a=self.group.debug(aes_key_ct)
            return aes_key_ct
        except Exception as e:
            print("Unexpected error:", str(e))

    def decrypt_secret_proxy(self, ct, cloud_pk, sk_cs, pxy_k_u):
        try:
            for user, keys in self.delegation.items():
                if pxy_k_u in keys:
                    intmed_value = self.cpabe.proxy_decrypt(cloud_pk, sk_cs, pxy_k_u, ct)
                    if intmed_value:
                        return intmed_value
                    else:
                        raise Exception('User attrs do not comply with access policy.')
            raise Exception('Delegation (proxy record) not found.')
        except Exception as e:
            print("Unexpected error:", str(e))


    def decrypt_secret_user(self, intmed, cloud_pk, sk_u):
        try:
            msg = self.cpabe.user_decrypt(cloud_pk, sk_u, intmed)
            return msg
        except Exception as e:
            print("Unexpected error:", str(e))

    def decrypt_text(self, ct, secret):
        try:
            k = extractor(secret)
            symcrypt = SymmetricCryptoAbstraction(k)
            text = symcrypt.decrypt(ct)
            return text
        except Exception as e:
            print("Unexpected error:", str(e))

    def revoke(self, user):
        try:
            exist_user = False
            for pk_u, u in self.users:
                if user==u:
                    exist_user = True
            if exist_user:
                if user in self.delegation:
                    self.delegation.pop(user, None)
                    return self.delegation
            else:
                raise Exception('User not found, please check and try again.')
        except Exception as e:
            print("Unexpected error:", str(e))
