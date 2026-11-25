#include <metal_stdlib>
#include <simd/simd.h>

using namespace metal;

template<typename T, size_t Num>
struct spvUnsafeArray
{
    T elements[Num ? Num : 1];

    thread T& operator [] (size_t pos) thread { return elements[pos]; }
    constexpr const thread T& operator [] (size_t pos) const thread { return elements[pos]; }
    threadgroup T& operator [] (size_t pos) threadgroup { return elements[pos]; }
    constexpr const threadgroup T& operator [] (size_t pos) const threadgroup { return elements[pos]; }
};
int dmsh_hmma16816_f16(thread const int& _42961, thread const int& _42962, thread const int& _42963, thread const int& _42964, thread const int& _42965, thread const int& _42966, thread const int& _42967, thread const int& _42968, thread const int& _42969, thread const int& _42970, thread int& _42971, threadgroup spvUnsafeArray<uint, 1024>& _34)
{
    uint _42974 = uint(int(uint(_42961) >> uint(2)));
    _34[_42962 + int(_42974)] = uint(_42963);
    if (_42974 > 3u)
    {
        _42971 = 0;
    }
    simdgroup_barrier(mem_flags::mem_threadgroup);
    _42971 = int(_34[_42962]);
    return int(_34[_42962 + 1]);
}
kernel void check(device const uint *in [[buffer(0)]], device uint *out [[buffer(1)]], uint lane [[thread_index_in_simdgroup]], uint sg [[simdgroup_index_in_threadgroup]],
                  uint gid [[thread_position_in_grid]])
{
    threadgroup spvUnsafeArray<uint, 1024> scr;
    int l = int(lane), blk = int(sg * 256);
    int a0 = int(in[gid * 8 + 0]), a1 = int(in[gid * 8 + 1]), a2 = int(in[gid * 8 + 2]), a3 = int(in[gid * 8 + 3]);
    int b0 = int(in[gid * 8 + 4]), b1 = int(in[gid * 8 + 5]), c0 = int(in[gid * 8 + 6]), c1 = int(in[gid * 8 + 7]);
    int d1;
    int d0 = dmsh_hmma16816_f16(l, blk, a0, a1, a2, a3, b0, b1, c0, c1, d1, scr);
    out[gid * 2] = uint(d0); out[gid * 2 + 1] = uint(d1);
}
