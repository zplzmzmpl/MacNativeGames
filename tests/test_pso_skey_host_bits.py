"""The pipeline parser rejects the former headset renderer's bits in existing lists."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
NVN = ROOT / 'games/totk/third_party/d2r_gfx/gfx/nvn'

PROBE = r'''
#import <Foundation/Foundation.h>
#include <stdio.h>
#include <stddef.h>
@interface NvShader : NSObject { @public char key[80]; int stage; } @end   /* the fields pso_skey_from reads (nvn_mtl.m) */
@implementation NvShader @end
#include "nvn_pso_skey.h"
int main(void) {
    unsigned bits[] = {0, 1, 2, 8, 12, 16, 32, 64, 128, 64 | 8};
    for (size_t i = 0; i < sizeof bits / sizeof *bits; i++) {
        pso_skey k; memset(&k, 0, sizeof k); k.k.a2c = bits[i];
        char hex[sizeof k * 2 + 1]; pso_skey_hex(&k, hex);
        pso_skey back; int r = pso_skey_parse(hex, &back);
        printf("%u %d %u\n", bits[i], r, r ? 0u : back.k.a2c);
    }
    printf("offset %zu size %zu\n", offsetof(pso_skey, k) + offsetof(pso_key, a2c), sizeof(pso_skey));
    return 0;
}
'''


@unittest.skipUnless(shutil.which('xcrun'), 'needs the Xcode command line tools')
class HostBits(unittest.TestCase):
    def test_a_row_with_host_bits_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / 'p.m').write_text(PROBE)
            build = subprocess.run(['xcrun', 'clang', '-w', '-fobjc-arc', f'-I{NVN}', f'-I{NVN / "include"}', str(tmp / 'p.m'), '-framework', 'Foundation', '-o', str(tmp / 'p')],
                                   capture_output=True, text=True)
            self.assertEqual(build.returncode, 0, build.stderr)
            lines = subprocess.run([str(tmp / 'p')], capture_output=True, text=True, check=True).stdout.splitlines()
        self.assertEqual(lines[-1], 'offset 268 size 544')   # where tools read a2c in a listed row (the lists' hex keys)
        for line in lines[:-1]:
            bits, result, back = map(int, line.split())
            with self.subTest(a2c=bits):
                if bits & (64 | 128):
                    self.assertEqual(result, -1)
                else:
                    self.assertEqual((result, back), (0, bits))

    def test_hdr_pipelines_are_kept_out_of_shared_lists(self):
        text = (NVN / 'nvn_mtl.m').read_text()
        adopt = text.split('static void pso_adopt(', 1)[1].split('\n}', 1)[0]
        adopt = re.sub(r'//[^\n]*', '', adopt)
        guard = re.search(r'if \(k->a2c & PSO_HDR\) \{([^{}]*)\}', adopt)
        self.assertIsNotNone(guard)
        self.assertRegex(guard[1], r'hm_put_id\(&g_pso, k, ps\);\s*g_pso_gen\+\+;')
        self.assertTrue(guard[1].strip().endswith('return;'))
        for record in ('pso_record(', 'pso_user_record(', 'pso_contribute('):
            self.assertGreater(adopt.index(record), guard.end())

if __name__ == '__main__':
    unittest.main()
