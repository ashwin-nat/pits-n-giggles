# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from typing import Final

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

# Precomputed Savitzky-Golay first-derivative coefficients.
#
# Generated with:
#   x = np.arange(w) - (w - 1)          # x in [-(w-1), 0], evaluate at rightmost point
#   A = np.vander(x, p+1, increasing=True)
#   e1 = [0, 1, 0, ...]
#   coeffs = A @ np.linalg.solve(A.T @ A, e1)
#
# Applied as:  d_energy_per_sample = dot(coeffs, energy_window)
# Scale to watts: power_w = d_energy_per_sample * 1000.0 / avg_dt_ms

SAVGOL_COEFFS: Final[dict[tuple[int, int], list[float]]] = {
    (9, 3): [
        -0.25084175084172955,
         0.2239057239057125,
         0.2935305435305242,
         0.11038961038959627,
        -0.17316017316017263,
        -0.40476190476189133,
        -0.43205868205866294,
        -0.10269360269359273,
         0.7356902356902136,
    ],
    (15, 3): [
        -0.13861655773421688,
         0.006458138811081149,
         0.08692750604516153,
         0.11469032057268436,
         0.10164535899831062,
         0.05969139792669953,
         0.0007272139625111862,
        -0.06334841628959431,
        -0.12063671622495775,
        -0.15923890923891904,
        -0.16725621872681895,
        -0.13278986808399695,
        -0.04394108070579328,
         0.11118892001245162,
         0.3444989106753976,
    ],
    (21, 3): [
        -0.08509003074219557,
        -0.023589936633412023,
         0.01939301481635347,
         0.04611440767046693,
         0.05882982599229125,
         0.059794853845190676,
         0.05126507529252988,
         0.03549607439767177,
         0.01474343522398236,
        -0.008737258165175454,
        -0.03269042170643721,
        -0.0548604713364389,
        -0.07299182299181606,
        -0.0848288926092049,
        -0.08811609612524096,
        -0.08059784947656023,
        -0.06001856859979848,
        -0.024122669431591637,
         0.0293454320914244,
         0.10264132003261389,
         0.19802057845534096,
    ],
}
