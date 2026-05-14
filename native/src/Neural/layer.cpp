#include "layer.h"
namespace DeepLr::Neural {
	Layer::Layer() {
		ntype = Null;
	}
	std::array<float, 10> Layer::ToOneHot(int32_t number) {
		if (number < 0 || number > 9) return std::array<float, 10>();
		std::array<float, 10> result = { 0.0f };
		result[number] = 1.0f;
		return result;
	}
}
