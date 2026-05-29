import oqs as _oqs

# Compatibility aliases
get_enabled_KEM_mechanisms = _oqs.get_enabled_kem_mechanisms
get_enabled_SIG_mechanisms = _oqs.get_enabled_sig_mechanisms

# Re-export everything else
from oqs import *
