#pragma once
#include "tensor.h"
#include <array>
#include "../data.h"
namespace DeepLr::Neural {
	class Layer {
	public:
		Layer();
		virtual Tensor3D Forward(const Tensor3D& input) = 0;
		virtual Tensor3D Backward(const Tensor3D& output) = 0;
		//virtual void Update(float lr) = 0;
		std::array<int32_t, 4> target;
		static std::array<float, 10> ToOneHot(int32_t number);
	protected:
		NeuralType ntype;
	};
}