#pragma once
#include "../data.h"
#include <vector>
#include <memory>
#include <random>
#include "layer.h"
#include "sample.h"
#include "loss.h"
namespace DeepLr::Neural {
	class Neural {
	public:
		Neural(const std::vector<NeuralBuild> & builds);
	private:
		std::vector<Layer*> neural;
		Loss loss;
		static void BuildNeural();
		float TrainBatch(const std::vector<std::shared_ptr<Sample>>& samples,float lr);
		void Train(std::vector<std::shared_ptr<Sample>>& samples,int32_t maxEpoch);
		static std::shared_ptr<std::mt19937> g;
	};
}