#pragma once
#include "layer.h"
namespace DeepLr::Neural {
	class BiLSTM : public Layer {
	public:
		BiLSTM();
		Tensor3D Forward(const Tensor3D& input) override;
		void SetShape(const TensorShape& lastshape, const TensorShape& shape) override;
	private:
		Tensor3D wf;//遗忘门权重
		Tensor3D bf;//遗忘门偏置
		Tensor3D wi;//输入门权重
		Tensor3D bi;//输入门偏置
		Tensor3D wg;//后选值权重
		Tensor3D bg;//后选值偏置
		Tensor3D wo;//输出门权重
		Tensor3D bo;//输出门偏置
		void Sigmoid(Tensor3D& input);
		void Tanh(Tensor3D& input);
	};
}