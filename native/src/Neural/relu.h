#pragma once
#include "layer.h"
namespace DeepLr::Neural {
	class Relu :public Layer {
	public:
		Relu();
		~Relu() = default;
		Tensor3D Forward(const Tensor3D& input, const std::array<int32_t, 4>& target) override;
		Tensor3D Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) override;
		void Update(float lr, int32_t batchSize) override {};
	private:
		Tensor3D oldx;
	};
}