import angr
import logging

from .resolver import IndirectJumpResolver

l = logging.getLogger("angr.analyses.cfg.indirect_jump_resolvers.x86_pe_iat")

class X86PeIatResolver(IndirectJumpResolver):
    def __init__(self, project):
        super(X86PeIatResolver, self).__init__(project, timeless=True)

    def filter(self, cfg, addr, func_addr, block, jumpkind):
        if not isinstance(self.project._simos, angr.simos.SimWindows):
            return False
        if jumpkind != "Ijk_Call":
            return False

        opnd = self.project.factory.block(addr).capstone.insns[-1].insn.operands[0]
        # Must be of the form: call ds:0xABCD
        if opnd.mem and opnd.mem.disp and not opnd.mem.base and not opnd.mem.index:
            return True
        return False

    def resolve(self, cfg, addr, func_addr, block, jumpkind):
        slot = self.project.factory.block(addr).capstone.insns[-1].insn.disp
        target = cfg._fast_memory_load_pointer(slot)
        if target is None:
            l.warning("Address %#x does not appear to be mapped", slot)
            return False, []

        if not self.project.is_hooked(target):
            return False, []

        dest = self.project.hooked_by(target)
        l.debug("Resolved target to %s", dest.display_name)
        return True, [target]
