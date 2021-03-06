#!/usr/bin/env python
#
# Intercept vmcall and provide singlestep() handler
#
# ie. single stepping near the end of a physical page
#     may lead to GDBError(mem) because default insn size
#     read by disasm engine is 15 bytes. We may be located
#     below 15 bytes from the end of the page.
#
from amoco.arch.x86  import cpu_x86 as am
from ramooflax.core  import VM, CPUFamily, log, GDBError
from ramooflax.utils import disassemble

def disasm_wrapper(addr, data):
    return am.disassemble(data, address=addr)

def disasm(vm):
    addr = vm.cpu.code_location()
    try:
        print disassemble(vm, disasm_wrapper, addr)
    except GDBError as e:
        if e.value == GDBError.mem:
            # consider page size to be 4K
            pg_sz = 1<<12
            nxt = (addr + pg_sz) & ~(pg_sz-1)
            sz = nxt - addr
            print disassemble(vm, disasm_wrapper, vm.cpu.code_location(), sz)
    except:
        pass

def hypercall(vm):
    log("info", "hypercall")
    return True

def sstep(vm):
    log("info", "sstep")
    print disasm(vm)
    return False

##
## Main
##
peer = "172.16.131.128:1337"
vm = VM(CPUFamily.Intel, peer)

log.setup(info=True, fail=True,
          gdb=False, vm=True,
          brk=True,  evt=False)

vm.attach()
vm.stop()

log("info", "install filters")
vm.cpu.filter_hypercall(hypercall)
vm.cpu.filter_singlestep(sstep)

log("info", "ramooflax ready!")
vm.interact2(dict(globals(), **locals()))
