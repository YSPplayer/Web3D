#pragma once
#include <memory>
#include "layer.h"
namespace DeepLr::Neural {
	struct BiLSTMPar {
		Tensor3D wf;//遗忘门权重
		Tensor3D bf;//遗忘门偏置
		Tensor3D wi;//输入门权重
		Tensor3D bi;//输入门偏置
		Tensor3D wg;//后选值权重
		Tensor3D bg;//后选值偏置
		Tensor3D wo;//输出门权重
		Tensor3D bo;//输出门偏置
	};
	class BiLSTM : public Layer {
	public:
		BiLSTM();
		Tensor3D Forward(const Tensor3D& input) override;
		Tensor3D Backward(const Tensor3D& output, const std::array<int32_t, 4>& target) override;
		void SetShape(const TensorShape& lastshape, const TensorShape& shape) override;
		void Update(float lr, int32_t batchSize) override;
	private:
		std::shared_ptr<BiLSTMPar> par;
		std::shared_ptr<BiLSTMPar> rpar;
		std::shared_ptr<BiLSTMPar> dpar;
		std::shared_ptr<BiLSTMPar> drpar;
		Tensor3D oldx;
		int32_t inputSize;
		int32_t hiddenSize;
		void Sigmoid(Tensor3D& input);
		void Tanh(Tensor3D& input);
	};
}
