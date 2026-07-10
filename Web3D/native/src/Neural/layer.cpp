#include "layer.h"
namespace DeepLr::Neural {
	Layer::Layer() {
		ntype = Null;
	}
	void Layer::SetShape(const TensorShape& lastshape, const TensorShape& shape) {
		this->lastshape = lastshape;
		this->shape = shape;
	}
	std::array<float, 10> Layer::ToOneHot(int32_t number) {
		if (number < 0 || number > 9) return std::array<float, 10>();
		std::array<float, 10> result = { 0.0f };
		result[number] = 1.0f;
		return result;
	}
}
