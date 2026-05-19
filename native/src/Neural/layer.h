#pragma once
#include "tensor.h"
#include <array>
#include "../data.h"
namespace DeepLr::Neural {
	class Layer {
	public:
		Layer();
		inline NeuralType GetNeuralType() const {
			return ntype;
		}
		NeuralBuild GetNeuralBuild() {
			return NeuralBuild(ntype, shape.c, shape.w, shape.h);
		};
		virtual void SetShape(const TensorShape& lastshape, const TensorShape& shape);
		virtual Tensor3D Forward(const Tensor3D& input) = 0;
		virtual Tensor3D Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) = 0;
		virtual void Update(float lr, int32_t batchSize) = 0;
		static std::array<float, 10> ToOneHot(int32_t number);
		TensorShape shape;
		TensorShape lastshape;
	protected:
		NeuralType ntype;
	};
}
