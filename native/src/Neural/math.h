#pragma once
#include <cmath>
namespace DeepLr::Neural {
	float Sigmoid(float x) {
		return std::exp(x) / (std::exp(x) + 1.0f);
	}
	float Tanh(float x) {
		return 1.0f - 2.0f / (std::exp(2 * x) + 1.0f);
	}
}