#$6 = {fp_ctxt = 0x0, edi = 0, esi = 7629208, ebp = 7757928, esp0 = 7757304, ebx = 6596532, edx = 2809425364, ecx = 7757392, eax = 13314892, idtIndex = 13, faultCode = 10260, eip = 1120, cs = 8, eflags = 78486}

define rtems-crash
    set $code = $arg0
    set $edi = ((const rtems_exception_frame*)$code)->edi
    set $esi = ((const rtems_exception_frame*)$code)->esi
    set $ebp = ((const rtems_exception_frame*)$code)->ebp
    set $esp0 = ((const rtems_exception_frame*)$code)->esp0
    set $ebx = ((const rtems_exception_frame*)$code)->ebx
    set $edx = ((const rtems_exception_frame*)$code)->edx
    set $ecx = ((const rtems_exception_frame*)$code)->ecx
    set $eax = ((const rtems_exception_frame*)$code)->eax
    set $eip = ((const rtems_exception_frame*)$code)->eip
    set $cs = ((const rtems_exception_frame*)$code)->cs
    set $eflags = ((const rtems_exception_frame*)$code)->eflags
end