#include "ctcloss.h"
#include <cmath>
#include <limits>

namespace DeepLr::Neural {
	CTCLoss::CTCLoss(const std::unordered_map<char, int32_t>& map):map(map) {
	}

	float CTCLoss::Forward(const Tensor3D& input, const std::string& target) {
		const int32_t T = input.Height();
		if (T <= 0) {
			return std::numeric_limits<float>::infinity();
		}

		const std::string ctc = ExpandCTC(target);
		const int32_t L = static_cast<int32_t>(ctc.size());
		if (L <= 0) {
			return std::numeric_limits<float>::infinity();
		}

		const float negInf = -std::numeric_limits<float>::infinity();
		const float eps = std::numeric_limits<float>::min();

		auto logAdd = [negInf](float a, float b) {
			if (a == negInf) return b;
			if (b == negInf) return a;
			if (a < b) {
				const float tmp = a;
				a = b;
				b = tmp;
			}
			return a + std::log1p(std::exp(b - a));
		};

		auto logProb = [&](int32_t t, int32_t s) {
			const auto it = map.find(ctc[s]);
			if (it == map.end()) {
				return negInf;
			}
			const float p = input.Get(0, t, it->second);
			if (p <= 0.0f) {
				return negInf;
			}
			return std::log(p < eps ? eps : p);
		};

		std::vector<std::vector<float>> alpha(T, std::vector<float>(L, negInf));
		alpha[0][0] = logProb(0, 0);
		if (L > 1) {
			alpha[0][1] = logProb(0, 1);
		}

		for (int32_t t = 1; t < T; ++t) {
			for (int32_t s = 0; s < L; ++s) {
				float sum = alpha[t - 1][s];
				if (s > 0) {
					sum = logAdd(sum, alpha[t - 1][s - 1]);
				}
				if (s > 1 && ctc[s] != CTC_BLANK && ctc[s] != ctc[s - 2]) {
					sum = logAdd(sum, alpha[t - 1][s - 2]);
				}
				if (sum != negInf) {
					alpha[t][s] = sum + logProb(t, s);
				}
			}
		}

		float result = alpha[T - 1][L - 1];
		if (L > 1) {
			result = logAdd(result, alpha[T - 1][L - 2]);
		}
		return result == negInf ? std::numeric_limits<float>::infinity() : -result;
	}

	std::string CTCLoss::ExpandCTC(const std::string& label, char blank) {
		if (label.empty()) {
			return std::string(1, blank);
		}
		std::string expanded;
		expanded.reserve(2 * label.size() + 1);
		expanded.push_back(blank);
		for (size_t i = 0; i < label.size(); ++i) {
			expanded.push_back(label[i]);
			expanded.push_back(blank);
		}
		return expanded;
	}
}
