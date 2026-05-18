#pragma once
#include "../data.h"
#include <vector>
#include <memory>
#include <random>
#include "layer.h"
#include "sample.h"
#include "loss.h"
#include <any>
namespace DeepLr::Neural {
	class Neural {
	public:
		Neural(TensorShape tensorShape,const std::vector<NeuralBuild>& builds);
		static std::shared_ptr<Neural> BuildDefaultNeural();
		void Train(std::vector<std::shared_ptr<Sample>>& samples, int32_t maxEpoch);
		void SaveModel(const std::string& filename);
	private:
		std::vector<Layer*> neural;
		Loss loss;
		Tensor3D Predict(const Tensor3D& input);
		static Tensor3D Predict(const Tensor3D& input,const std::vector<NeuralBuild>& builds, const std::vector<std::any>& cores);//推理模型
		float TrainBatch(const std::vector<std::shared_ptr<Sample>>& samples,float lr);
		bool WriteToBinaryFile(const std::string& filename, const std::vector<char>& buffer);
		static std::shared_ptr<std::mt19937> g;
	};
}